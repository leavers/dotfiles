# 内核 HTTP API

## 基本约定

- base：`http://127.0.0.1:<port>`（本机 40111），所有接口都是 `POST` + JSON body
- 请求头：`Content-Type: application/json`，写操作用 `Authorization: Token <token>`
- 返回统一信封：`{"code":0,"msg":"","data":...}`；`code != 0` 时读 `msg`

## 鉴权实况（实测，容易踩）

- **只读接口不带 token 也能过**：`query/sql`、`notebook/lsNotebooks`、`export/exportMdContent` 本机实测均正常。
- **写接口需要正确 token**：`block/updateBlock`、`block/appendBlock`、`block/deleteBlock`、`filetree/createDocWithMd`。
- `<workspace>/conf/conf.json` 里的 `api.token` **可能不等于运行实例正在用的 token**：带上它会得到 `Auth failed [header: Authorization]`。所以读操作别带、写操作用用户在 GUI 里给出的 token（`SIYUAN_TOKEN` 环境变量），不要写进文件或回答。

## 端点清单

读：

| 端点 | 用途 | body |
| --- | --- | --- |
| `/api/system/version` | 连通性与内核版本 | `{}` |
| `/api/notebook/lsNotebooks` | 笔记本列表（笔记本 ID 从这里拿） | `{}` |
| `/api/query/sql` | 只读 SQL，探查块结构（见 `sql-and-blocks.md`） | `{"stmt":"SELECT ..."}` |
| `/api/export/exportMdContent` | 导出文档 markdown | `{"id":"<docID>"}` |
| `/api/filetree/getDoc` | 文档/块的 DOM 与内容 | `{"id":"...","mode":0}` |
| `/api/block/getChildBlocks` | 直接/全部子块，**顺序可靠**：对文档返回该文档下所有块（含标题后代），对标题块返回其后代 | `{"id":"..."}` |
| `/api/attr/getBlockAttrs` | 块属性（含自定义属性） | `{"id":"..."}` |

写：

| 端点 | 用途 | body |
| --- | --- | --- |
| `/api/block/updateBlock` | 更新单个块；`id` 传文档块 ID 时是整体替换文档内容 | `{"id":"...","dataType":"markdown","data":"..."}` |
| `/api/block/appendBlock` | 追加到父块末尾（文档 → 文档末尾） | `{"parentID":"<docID>","dataType":"markdown","data":"..."}` |
| `/api/block/deleteBlock` | 删除块；**子块会上移而不是级联删除** | `{"id":"..."}` |
| `/api/block/insertBlock` / `prependBlock` | 指定位置插入 | 同上 + `"previousID"` |
| `/api/filetree/createDocWithMd` | 新建文档；**目标已存在时不会覆盖内容** | `{"notebook":"<boxID>","path":"/父文档/标题","markdown":"...","id":"可选"}` |

## 返回体处理（省上下文的关键）

- **写接口的响应可能极大**：`updateBlock` / `appendBlock` 会回传整个事务的 `doOperations`，本机实测一次 **219 KB**。脚本里只取 `code`/`msg` 打印，不要把响应整段读进上下文。
- 常见错误串：`Auth failed [header: Authorization]`（token 问题）、`no such table: X`（SQL 表名错，见 `sql-and-blocks.md`）。

## 构造请求的注意事项

- **含中文或大段 markdown 的 body 一定走 UTF-8 文件 + `python3`（`json.dumps` + `urllib`）**，不要塞进 shell 单引号或 `curl --data`：引号、转义、编码都会出问题，非 ASCII 也不该经 shell 管道传递。
- 纯 ASCII 的小 body 可以直接 `curl --data '{"stmt":"SELECT ..."}'`；SQL 里的中文可以用 `\uXXXX` 转义内联（例如 `\u65b0\u7248\u672c\u7279\u6027` = 新版本特性）。
- 幂等性：读接口随便调；**写接口失败后先回读确认状态再决定是否重试**，避免重复插入。
- 大 markdown 写入前先落盘成文件（`/tmp/x.md` 或仓库内 scratch），便于重试与 diff。

## 最小可用示例

```bash
PORT=40111
curl -s -m 5 -X POST http://127.0.0.1:$PORT/api/system/version
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"stmt":"SELECT id, hpath, content FROM blocks WHERE type = '"'"'d'"'"' AND hpath LIKE '"'"'%Zig%'"'"'"}' \
  http://127.0.0.1:$PORT/api/query/sql
```

但日常请直接用 `scripts/sy.py`，省掉上面所有转义：

```bash
python3 scripts/sy.py sql "SELECT id, hpath FROM blocks WHERE type='d' AND hpath LIKE '%Zig%'"
python3 scripts/sy.py export 20240622184956-rj3itix -o /tmp/doc.md
```
