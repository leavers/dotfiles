---
name: siyuan-flatpak
description: Operate the local SiYuan instance installed via Flatpak when the `siyuan` CLI is unusable — talk to the running kernel over HTTP, query notes with SQL, rewrite documents safely with backup and read-back verification. Use for reading/editing/searching this machine's SiYuan notes (极致工程, Zig/Python docs), or when `flatpak run`/`siyuan` fails with "Unable to allocate instance id".
argument-hint: ["<task> e.g. 'read 极致工程/Zig/Cheatsheet', 'rewrite note X in Chinese', 'find blocks about PEP 695'"]
---

# SiYuan (Flatpak) — 操作手册

适用环境：SiYuan 以 Flatpak 安装（`org.b3log.siyuan`），GUI 正在运行，笔记在 `/home/gaochang/Documents/SiYuan`，内核版本 v3.8.6。

## 第一步：三步自检

```bash
ps -eo pid,args | grep -o 'SiYuan-Kernel serve --port [0-9]*' | head -1 # ① 拿内核端口（本机为 40111）
curl -s -m 5 -X POST http://127.0.0.1:40111/api/system/version # ② 确认可达（返回 {"code":0,"data":"3.8.6"}）
python3 .agents/skills/siyuan-flatpak/scripts/sy.py info # ③ 端口 / 工作区 / token / 版本一次看全
```

## 铁律（踩过的坑）

1. **不要用 `siyuan` 或 `flatpak run`**：此环境 flatpak 起不来（`error: Unable to allocate instance id`，根因是 `/run/user/1000/.flatpak` 只读）。改走内核 HTTP API。
2. **不要起第二个内核**（`SiYuan-Kernel serve -w <workspace>`）：GUI 已打开该工作区，第二个实例会抢文件锁与索引。只读 CLI 子命令除外（见 `references/environment.md`）。
3. **不要直接改 `data/**/*.sy` 文件**：内核持有索引，绕过 API 会不一致。
4. **写笔记前先备份、写完后必须回读验证**：`sy.py export <docID> -o /tmp/backup.json`，再比对章节/行数/关键词。
5. **不要把 API token 写进文件、日志或回答**。需要时从 `SIYUAN_TOKEN` 环境变量取；读操作通常不鉴权即可用。

## 任务路由（按需读，不要一次性全读）

| 你要做的事 | 读这个 |
| --- | --- |
| 弄清为什么 CLI 不能用、怎么拿端口/工作区/版本、哪些路径可写 | `references/environment.md` |
| 调内核 HTTP API：端点清单、鉴权坑、返回体处理 | `references/http-api.md` |
| 用 SQL 查笔记本/文档/块、验证改动结果 | `references/sql-and-blocks.md` |
| 新建 / 整体重写 / 追加 / 删除文档内容 | `references/document-editing.md` |
| 直接动手 | `scripts/sy.py --help`（子命令见下） |

## 常用动作

```bash
# skill 目录可能在本仓库（.agents/skills/...）或全局（~/.agents/skills/...）
S="${SIYUAN_SKILL_DIR:-.agents/skills/siyuan-flatpak}/scripts/sy.py"

python3 $S --help # 全部子命令
python3 $S info # 环境体检
python3 $S notebooks # 笔记本列表
python3 $S find "新版本特性" # 按标题/hpath 找文档
python3 $S sql "SELECT id,hpath FROM blocks WHERE type='d' AND hpath LIKE '%Zig%'" # 只读 SQL：按 hpath 或标题找文档
DOC_ID=20261012063916-nvid2gb # 示例：Zig/新版本特性；换成你要操作的文档 ID
python3 $S tree "$DOC_ID" # 文档的标题层级
python3 $S export "$DOC_ID" -o /tmp/doc.md # 导出 markdown（自动剥离 front matter）
python3 $S replace "$DOC_ID" /tmp/doc.md # 整体重写：清空内容块 + 追加（推荐）
python3 $S append "$DOC_ID" /tmp/section.md # 追加一节
python3 $S write "$DOC_ID" /tmp/doc.md # updateBlock 到文档块（整体替换，谨慎）
BLOCK_ID=20261012064615-7dnwgzp # 示例：用 tree / child 拿到的块 ID
python3 $S delete "$BLOCK_ID" # 按块 ID 删除（自下而上）
```

## 最小心智模型

- 笔记的真相在内核里，通过 HTTP API 读写：`POST /api/<area>/<action>` + JSON body。
- 文档是一棵树：文档块（`type='d'`）→ 标题块（`h`/`h1..h6`）→ 段落/代码块等；每个块都有稳定 ID。
- 块之间的关系靠 `blocks` 表的 `id / parent_id / root_id / hpath / box` 表达，SQL 是最快的探查手段（`/api/query/sql`）。
- 写作类任务的成功标准是「回读内容与预期一致」，不是「接口返回 code:0」。
