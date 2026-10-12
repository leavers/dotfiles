#!/usr/bin/env python3
"""SiYuan (Flatpak) 内核 API 小工具，只依赖 Python 标准库。

先决条件：SiYuan GUI 正在运行（内核监听本机端口）。见 ../references/environment.md

用法：python3 sy.py <command> [args]

  info                                环境体检：端口 / 工作区 / token / 版本
  notebooks                           笔记本列表（id / name / closed）
  find <关键词> [--blocks]             找文档（默认）或包含该词的块
  sql <SQL语句> [--json] [--limit N]   执行只读 SQL
  tree <docID>                        列出文档的标题层级
  child <blockID>                     列出某块的直接子块
  export <docID> [-o FILE] [--raw]    导出 markdown（默认剥离 front matter）
  append <docID> <md文件>             追加 markdown 到文档末尾
  write <docID> <md文件>              用 updateBlock 整体替换文档内容
  replace <docID> <md文件>            清空文档内容块后追加（推荐的整体重写）
  clear <docID>                       清空文档内容块（自下而上删，保留文档本身）
  delete <blockID> [...]              自下而上删除指定块

环境变量：SIYUAN_API（base URL）、SIYUAN_TOKEN（写操作需要）、SIYUAN_WORKSPACE
"""

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

ID_RE = re.compile(r"^[0-9A-Za-z\-]{4,64}$")
DEPLOYED_KERNEL = "/var/lib/flatpak/app/org.b3log.siyuan/current/active/files/siyuan/resources/kernel/SiYuan-Kernel"


# ---------------------------------------------------------------- 环境探测
def discover_base():
    base = os.environ.get("SIYUAN_API")
    if base:
        return base.rstrip("/")
    port = None
    try:
        out = subprocess.run(
            ["ps", "-eo", "args"], capture_output=True, text=True, timeout=10
        ).stdout
        match = re.search(r"SiYuan-Kernel serve .*--port (\d+)", out)
        if match:
            port = match.group(1)
    except Exception:
        pass
    return "http://127.0.0.1:%s" % (port or "40111")


def token():
    return os.environ.get("SIYUAN_TOKEN", "")


def workspace_dir():
    path = os.environ.get("SIYUAN_WORKSPACE")
    if path:
        return path
    try:
        out = subprocess.run(
            [DEPLOYED_KERNEL, "workspace", "list"], capture_output=True, text=True, timeout=30
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip().splitlines()[0].strip()
    except Exception:
        pass

    guess = os.path.expanduser("~/Documents/SiYuan")
    return guess if os.path.isdir(guess) else None


def disk_token():
    wd = workspace_dir()
    if not wd:
        return None
    conf = os.path.join(wd, "conf", "conf.json")
    try:
        with open(conf, encoding="utf-8") as handle:
            return (json.load(handle).get("api") or {}).get("token")
    except Exception:
        return None


# ---------------------------------------------------------------- HTTP
def api(path, payload=None, auth=False, timeout=120):
    base = discover_base()
    data = json.dumps(payload or {}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if auth and token():
        headers["Authorization"] = "Token " + token()
    req = urllib.request.Request(base + path, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"code": -1, "msg": "HTTP %s: %s" % (exc.code, exc.read()[:200])}
    except Exception as exc:  # noqa: BLE001
        return {"code": -1, "msg": "%s: %s" % (type(exc).__name__, exc)}


def sql_rows(stmt):
    result = api("/api/query/sql", {"stmt": stmt})
    if result.get("code") != 0:
        raise SystemExit("SQL 失败: %s" % result.get("msg"))
    return result.get("data") or []


def check_id(value, label="ID"):
    if not ID_RE.match(value or ""):
        raise SystemExit("%s 不合法: %r" % (label, value))
    return value


# ---------------------------------------------------------------- 输出
def dump(value, limit=60):
    if isinstance(value, list):
        shown = value[:limit]
        text = json.dumps(shown, ensure_ascii=False, indent=2)
        if len(value) > limit:
            text += "\n… 共 %d 条，仅显示前 %d 条" % (len(value), limit)
        print(text)
    else:
        print(json.dumps(value, ensure_ascii=False, indent=2))


def print_table(rows, columns=None):
    if not rows:
        print("(无结果)")
        return
    columns = columns or list(rows[0].keys())
    widths = {c: max(len(str(c)), max(len(str(r.get(c, ""))) for r in rows)) for c in columns}
    print("  ".join(str(c).ljust(widths[c]) for c in columns))
    print("  ".join("-" * widths[c] for c in columns))
    for row in rows:
        print("  ".join(str(row.get(c, "")).ljust(widths[c]) for c in columns))


# ---------------------------------------------------------------- 文档操作
def export_doc(doc_id, strip=True):
    result = api("/api/export/exportMdContent", {"id": check_id(doc_id)})
    if result.get("code") != 0:
        raise SystemExit("导出失败: %s" % result.get("msg"))
    content = (result.get("data") or {}).get("content", "")
    if not strip:
        return content
    lines = content.split("\n")
    if lines and lines[0].strip() == "---":
        for index in range(1, min(len(lines), 40)):
            if lines[index].strip() == "---":
                return "\n".join(lines[index + 1:]).lstrip("\n")
    return content


def child_ids(block_id):
    return [
        row["id"]
        for row in sql_rows(
            "SELECT id FROM blocks WHERE parent_id = '%s' ORDER BY sort, id" % check_id(block_id)
        )
    ]


def child_blocks(block_id):
    """按真实文档顺序返回直接子块（SQL 的 sort 不可靠，见 references/sql-and-blocks.md）。"""
    result = api("/api/block/getChildBlocks", {"id": check_id(block_id)})
    if result.get("code") != 0:
        raise SystemExit("getChildBlocks 失败: %s" % result.get("msg"))
    return result.get("data") or []


def delete_subtree(block_id, depth=0):
    """自下而上删除：先删后代，再删自己（SiYuan 删标题块不会级联删子块）。"""
    for kid in child_ids(block_id):
        delete_subtree(kid, depth + 1)
    result = api("/api/block/deleteBlock", {"id": block_id}, auth=True)
    print("%sdel %s -> code=%s %s" % ("  " * depth, block_id, result.get("code"), result.get("msg")))


def clear_doc(doc_id):
    children = child_ids(doc_id)
    if not children:
        print("文档没有内容块，无需清理")
    for kid in children:
        delete_subtree(kid)


def append_md(doc_id, markdown):
    result = api(
        "/api/block/appendBlock",
        {"parentID": check_id(doc_id), "dataType": "markdown", "data": markdown},
        auth=True,
    )
    print("appendBlock -> code=%s msg=%s" % (result.get("code"), result.get("msg")))
    return result.get("code") == 0


def write_md(doc_id, markdown):
    result = api(
        "/api/block/updateBlock",
        {"id": check_id(doc_id), "dataType": "markdown", "data": markdown},
        auth=True,
    )
    print("updateBlock -> code=%s msg=%s" % (result.get("code"), result.get("msg")))
    return result.get("code") == 0


def structure(doc_id):
    rows = sql_rows(
        "SELECT (SELECT COUNT(*) FROM blocks WHERE root_id='{0}' AND type='h' AND subtype='h1') AS h1,"
        " (SELECT COUNT(*) FROM blocks WHERE root_id='{0}' AND type='h' AND subtype='h2') AS h2,"
        " (SELECT COUNT(*) FROM blocks WHERE root_id='{0}' AND type='h' AND subtype='h3') AS h3,"
        " (SELECT COUNT(*) FROM blocks WHERE root_id='{0}' AND type='c') AS code,"
        " (SELECT COUNT(*) FROM blocks WHERE root_id='{0}') AS total".format(check_id(doc_id))
    )
    title = sql_rows("SELECT content FROM blocks WHERE id='%s'" % check_id(doc_id))
    return {"title": title[0]["content"] if title else None, "structure": rows[0] if rows else {}}


def read_md_file(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


# ---------------------------------------------------------------- 命令
def cmd_info(_):
    base = discover_base()
    version = api("/api/system/version")
    print("base            :", base)
    print("kernel version  :", version.get("data") if version.get("code") == 0 else version)
    wd = workspace_dir()
    print("workspace       :", wd or "(未探测到)")
    env_tok = bool(token())
    disk = disk_token()
    print("token (env)     :", "已设置" if env_tok else "未设置")
    print("token (conf.json):", "存在但未必被运行实例接受" if disk else "无")
    if env_tok:
        probe = api("/api/block/getChildBlocks", {"id": "20240622184956-rj3itix"}, auth=True)
        print("写权限探测      :", "OK" if probe.get("code") == 0 else probe.get("msg"))


def cmd_notebooks(_):
    result = api("/api/notebook/lsNotebooks")
    notebooks = (result.get("data") or {}).get("notebooks") or []
    print_table(notebooks, ["id", "name", "closed"])


def cmd_find(argv):
    blocks = "--blocks" in argv
    words = [a for a in argv if not a.startswith("--")]
    if not words:
        raise SystemExit("用法: find <关键词> [--blocks]")
    keyword = words[0].replace("'", "''")
    if blocks:
        rows = sql_rows(
            "SELECT id, type, root_id, hpath, substr(content,1,60) AS c FROM blocks "
            "WHERE content LIKE '%%%s%%' LIMIT 40" % keyword
        )
    else:
        rows = sql_rows(
            "SELECT id, box, hpath, content FROM blocks WHERE type='d' AND "
            "(hpath LIKE '%%%s%%' OR content LIKE '%%%s%%') ORDER BY hpath LIMIT 40" % (keyword, keyword)
        )
    print_table(rows)


def cmd_sql(argv):
    as_json = "--json" in argv
    limit = 60
    words = []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--limit":
            limit = int(argv[index + 1])
            index += 2
            continue
        if not arg.startswith("--"):
            words.append(arg)
        index += 1
    if not words:
        raise SystemExit("用法: sql \"SELECT ...\"")
    rows = sql_rows(" ".join(words))
    if as_json:
        dump(rows, limit=limit)
    else:
        print_table(rows)
        print("(%d 行)" % len(rows))


def cmd_tree(argv):
    """列出文档的标题结构。

    注意：getChildBlocks 对文档返回的列表**已经包含各标题块的后代**（实测 h3 也在其中），
    所以这里只遍历一层、按 subType 缩进并用 seen 去重；不要递归，否则标题会重复出现。
    """
    doc_id = check_id(argv[0], "docID")
    seen = set()
    for item in child_blocks(doc_id):
        if item.get("type") != "h":
            continue
        block_id = item.get("id")
        if block_id in seen:
            continue
        seen.add(block_id)
        level = int((item.get("subType") or "h2")[1:])
        print("%s%s  (%s)" % ("  " * max(level - 2, 0), item.get("content") or "", block_id))


def cmd_child(argv):
    for item in child_blocks(argv[0]):
        text = (item.get("content") or "").replace("\n", " ")[:60]
        print("%-4s %-4s %s  (%s)" % (item.get("type"), item.get("subType") or "", text, item.get("id")))


def cmd_export(argv):
    doc_id = check_id(argv[0], "docID")
    raw = "--raw" in argv
    content = export_doc(doc_id, strip=not raw)
    if "-o" in argv:
        path = argv[argv.index("-o") + 1]
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        print("已写入 %s（%d 字符，%d 行）" % (path, len(content), content.count("\n")))
    else:
        print(content)


def cmd_append(argv):
    doc_id = check_id(argv[0], "docID")
    if append_md(doc_id, read_md_file(argv[1])):
        dump(structure(doc_id))


def cmd_write(argv):
    doc_id = check_id(argv[0], "docID")
    if write_md(doc_id, read_md_file(argv[1])):
        dump(structure(doc_id))


def cmd_replace(argv):
    doc_id = check_id(argv[0], "docID")
    markdown = read_md_file(argv[1])
    clear_doc(doc_id)
    if append_md(doc_id, markdown):
        dump(structure(doc_id))


def cmd_clear(argv):
    clear_doc(check_id(argv[0], "docID"))


def cmd_delete(argv):
    for block_id in argv:
        delete_subtree(check_id(block_id, "blockID"))


COMMANDS = {
    "info": cmd_info,
    "notebooks": cmd_notebooks,
    "find": cmd_find,
    "sql": cmd_sql,
    "tree": cmd_tree,
    "child": cmd_child,
    "export": cmd_export,
    "append": cmd_append,
    "write": cmd_write,
    "replace": cmd_replace,
    "clear": cmd_clear,
    "delete": cmd_delete,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return
    command = sys.argv[1]
    if command not in COMMANDS:
        raise SystemExit("未知命令 %r；可用：%s" % (command, ", ".join(sorted(COMMANDS))))
    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
