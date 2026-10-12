# 改写文档内容

## 决策树

| 目标 | 做法 |
| --- | --- |
| 新建文档 | `/api/filetree/createDocWithMd`（`notebook` + `path` + `markdown`） |
| **整篇重写（最常用）** | 清空内容块 + `appendBlock` → `sy.py replace <docID> file.md` |
| 追加一节 | `appendBlock` → `sy.py append <docID> file.md` |
| 只改一段 | `updateBlock`（`dataType=markdown`，`id` = 该块 ID） |
| 只改标题 | `updateBlock`（`id` = **文档块** ID，`data` = 新的标题文本） |
| 删块 | `deleteBlock`（注意子块上移，见下） |

## 必须知道的行为（均已实测）

1. **`createDocWithMd` 不会覆盖已存在的文档**：内核实现中，若 `hpath` 命中的文档已存在，直接返回现有 ID 而**不写 markdown**。不要用它「更新」文档。
2. **`updateBlock` 作用在文档块上 = 整体替换文档内容**（返回体很大，见 `http-api.md`）。以 `>` 或 `## ` 开头的 markdown 不会动文档标题；若 markdown 以 `# 标题` 开头，第一个 h1 会成为文档标题块。**要保住原文档名，就别写 h1。**
3. **删除标题块不会删除其子块**：删掉 `h1`/`h2` 后，其下章节内容会**上移**成为父级的直接子块。所以「清空文档」必须**自下而上**删除（先叶子、后标题）；`sy.py clear/replace` 已按此实现。
4. **导出内容带 front matter**：`exportMdContent` 返回的 markdown 以
   ```
   ---
   title: 文档名
   date: ...
   lastmod: ...
   ---
   ```
   开头，回写前必须剥离（`sy.py export` 默认剥离，`--raw` 保留原始）。
5. **导出 → 回写是有损的规范化**：行内代码两侧空格、列表缩进等会被重整，行数接近但字符数会变。验证要比「章节数 / 块数 / 关键词」，不要逐字节比。

## 推荐工作流

```bash
# skill 目录可能在本仓库（.agents/skills/...）或全局（~/.agents/skills/...）
S="${SIYUAN_SKILL_DIR:-.agents/skills/siyuan-flatpak}/scripts/sy.py"

# 1) 备份 + 现状勘察
python3 $S export <docID> -o /tmp/backup-<docID>.md
python3 $S tree <docID>

# 2) 准备新内容（写进仓库内 scratch，UTF-8，无 BOM）
#    - 顶层用 ## 分节，避免 h1 与文档标题冲突
#    - markdown 表格里正文竖线转义成 \|
#    - 代码块用三反引号 + 语言标签

# 3) 写入
python3 $S replace <docID> /tmp/new.md      # 清空 + 追加（推荐）
python3 $S append  <docID> /tmp/section.md  # 只在末尾追加
python3 $S write   <docID> /tmp/new.md      # updateBlock 到文档块（整体替换）

# 4) 回读验证（replace/append 会自动打印一份结构统计）
python3 $S export <docID> -o /tmp/readback.md
python3 $S sql "SELECT ... 结构统计 ..."

# 5) 清理 scratch，确认 git status 干净
```

## 回滚手段（按优先级）

1. 自己导出的 markdown 备份 —— 最快：把备份文件再 `replace` 回去。
2. SiYuan 自带文档历史（GUI 右下角「文档历史」）。
3. `repo` 快照 / 数据历史 —— 粒度粗，兜底用。

## 写内容的格式约定（SiYuan 侧）

- 文档标题存在文档块里；正文从 `##` 起层级最自然。
- 支持表格、引用、任务列表、代码块（带语言标签）、`kbd`/高亮等行内样式。
- 表格单元格里的 `|` 必须写作 `\|`。
- i18n/UI 无关的长文建议加一个开头的 `>` 引用块说明来源与验证方式（本仓库既有文档就是这个风格）。

## 验证清单

- [ ] 文档 ID 与标题未变（回读 `hPath` 与文档块 `content`）
- [ ] h2/h3 章节数量符合预期
- [ ] 代码块数量符合预期
- [ ] 新关键词出现、旧内容标记词消失
- [ ] `git status` 干净（scratch 已删）
