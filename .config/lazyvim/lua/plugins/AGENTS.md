# AGENTS.md — LazyVim 插件配置（dotfiles 管理）

## 用途

本目录通过 GitHub 个人仓库 [dotfiles](.) 统一管理 LazyVim 用户插件配置，
部署目标是 `~/.config/lazyvim/lua/plugins/`。

## 部署方式

- 本目录下的 `*.lua` 以**符号链接（绝对路径）**部署到
  `~/.config/lazyvim/lua/plugins/<同名>.lua`：

  ```sh
  ln -s ~/Projects/dotfiles/.config/lazyvim/lua/plugins/<file>.lua \
        ~/.config/lazyvim/lua/plugins/<file>.lua
  ```

- 本 `AGENTS.md` 也按同样方式链接到 `~/.config/lazyvim/lua/plugins/AGENTS.md`
  （lazy.nvim 只加载 `*.lua`，不会误加载它）。
- 部署是**按机器选择性的**：本目录中的文件不一定全部链接到每台机器
  （如 augment.lua / avante.lua / codeium.lua 在当前机器未部署）。
- 仓库路径若移动，所有绝对路径软链接需重建。

## 规则

- 所有改动直接在本仓库的真实文件上进行并提交推送；`~/.config/lazyvim`
  下的链接与真实文件是同一 inode，在那里编辑等价于在这里编辑，但容易
  忘记回仓库提交，导致换机丢失——**不要**只在本地留改动。
- 新增插件配置：文件放本目录 → 建软链接 → 重启 nvim 验证合并结果
  （如 headless 检查：`nvim --headless "+lua print(vim.inspect(LazyVim.opts('neovim/nvim-lspconfig').servers))" +qa`）。
- 配置必须机器可移植：不硬编码机器相关绝对路径、不放密钥；依赖外部工具
  （mason 包、系统命令等）时在注释中说明。
- 未由本目录管理的本地文件（如 LazyVim 自带的 `example.lua`）可能在
  `~/.config/lazyvim/lua/plugins/` 中存在，配置不得依赖它们。

## 当前文件

| 文件 | 作用 | 本机已部署 |
|---|---|---|
| `colorscheme.lua` | catppuccin 主题（纯黑背景） | 是 |
| `diffview.lua` | diffview.nvim 按键 | 是 |
| `spell.lua` | 拼写检查豁免中文（CJK） | 是 |
| `python.lua` | 关闭 pylsp 内置 pycodestyle（与项目 ruff line-length=100 对齐） | 是 |
| `mason-workaround.lua` | mason 变通配置 | 否 |
| `augment.lua` / `avante.lua` / `codeium.lua` | AI 插件备选 | 否 |
