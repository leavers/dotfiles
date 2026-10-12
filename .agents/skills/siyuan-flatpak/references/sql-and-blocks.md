# SQL 与块模型

内核内嵌 SQLite，可以直接用 SQL 探查笔记结构：`POST /api/query/sql`，body `{"stmt":"SELECT ..."}`。
**只允许 SELECT**；写语句会被拒绝——改内容只能走 block 类接口（见 `document-editing.md`）。

## 表名坑（实测）

- `notebooks` 表**不存在**：`no such table: notebooks`
- `boxes` 表**不存在**：`no such table: boxes`
- 拿笔记本列表请用 `/api/notebook/lsNotebooks`；在 SQL 里标识笔记本用 `blocks.box`（值就是笔记本 ID）

## `blocks` 常用字段

| 字段 | 含义 |
| --- | --- |
| `id` | 块 ID；文档 ID 形如 `YYYYMMDDHHmmss-xxxxxxx`，前缀即创建时间 |
| `parent_id` | 直接父块；文档的直属子块，其 `parent_id` 等于文档 ID |
| `root_id` | 所属文档 ID——统计「某文档下所有块」用它 |
| `box` | 笔记本 ID |
| `path` | 文件系统路径，如 `/20240622184956-rj3itix.sy` |
| `hpath` | 人类可读层级路径，如 `/Python/新版本特性` |
| `content` | 块内容（文档块=标题、标题块=标题文本、代码块=代码） |
| `type` | 块类型（见下表） |
| `subtype` | 子类型（标题的 `h1`..`h6` 等） |
| `sort` | 同级排序 |
| `created` / `updated` | 时间戳字符串 `YYYYMMDDHHmmss` |
| `ial` | 内联属性（自定义属性都在这里） |

## type / subtype

| type | 含义 |
| --- | --- |
| `d` | 文档块 |
| `h` | 标题块，`subtype` = `h1`..`h6` |
| `p` | 段落 |
| `c` | 代码块 |
| `l` | 列表容器；`i` 列表项 |
| `b` | 引用块 |
| `t` | 表格 |
| `m` | 数学公式块 |
| `s` | 超级块 |
| `query_embed` | 嵌入块（查询/引述等） |

## 常用查询片段

```sql
-- 按标题或层级路径找文档
SELECT id, box, hpath, content FROM blocks
WHERE type = 'd' AND (hpath LIKE '%关键词%' OR content LIKE '%关键词%');

-- 看某文档的直属子块（了解它的章节结构）
SELECT id, type, sort, substr(content,1,60) AS c FROM blocks
WHERE parent_id = '<docID>' ORDER BY sort, id;

-- 统计某文档下所有块（改动后的规模校验）
SELECT COUNT(*) FROM blocks WHERE root_id = '<docID>';

-- 结构统计（重写文档后的标准验证）
SELECT
  (SELECT COUNT(*) FROM blocks WHERE root_id='<docID>' AND type='h' AND subtype='h1') AS h1,
  (SELECT COUNT(*) FROM blocks WHERE root_id='<docID>' AND type='h' AND subtype='h2') AS h2,
  (SELECT COUNT(*) FROM blocks WHERE root_id='<docID>' AND type='c') AS code_blocks,
  (SELECT COUNT(*) FROM blocks WHERE root_id='<docID>') AS total;

-- 定位需要修改的具体段落
SELECT id, type, parent_id, substr(content,1,80) FROM blocks
WHERE root_id='<docID>' AND content LIKE '%待改文本%';

-- 某个笔记本下的文档清单
SELECT id, hpath, content, updated FROM blocks WHERE box='<boxID>' AND type='d' ORDER BY hpath;
```

## 陷阱

1. **同一段文字可能查到两条**：列表项块（`i`）和它内部的段落块（`p`）内容相同，是父子关系而非重复内容。按 ID 更新其中一条即可，另一条会同步（实测：更新 `p` 后 `i` 的 `content` 也变为新值）。
2. **`sort` 只在同级内可比**，且同值并不罕见（本机见过多个块 `sort=5`），不要用它做全局排序。
3. **删块不会级联删子块**（子块上移），因此「清空文档」必须自下而上删——见 `document-editing.md`。
4. `hpath` 是文档级路径，段落/代码块也带该字段（表示它属于哪篇文档）。
5. 查询结果默认可能被截断（响应里带 `limit` / `truncated` 字段），统计类需求用 `COUNT(*)` 而不是数数组长度。
6. **`sort` 不能用来还原文档顺序**：同一层级的块 `sort` 常常相同（本机实测一组 h2 全是 `sort=5`），`ORDER BY sort` 会退化成按 id（即创建时间）排序，顺序是错的。要按真实文档顺序遍历，用 `/api/block/getChildBlocks`——它的返回顺序可靠。
7. **`getChildBlocks` 与 SQL `parent_id` 语义不同，别混用**：对文档调用 `getChildBlocks` 返回的是**该文档下的所有块**（本机实测 126 项，包含 h3、列表、代码块，按文档顺序），而 SQL 里 `parent_id = <docID>` 只有 8 个块（引用块 + 7 个 h2，严格的树父子关系）。因此：
   - 要「文档顺序」（列标题结构）→ 一次 `getChildBlocks(doc)` + 按 `subType` 缩进，**不要再递归**（会重复）；
   - 要「严格树结构」或删子树 → SQL `parent_id` 递归（`sy.py clear` / `delete` 走这条）。
