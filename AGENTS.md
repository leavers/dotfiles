# AGENTS.md — 个人 dotfiles 仓库

## 简介

个人 dotfiles 仓库，统一管理各工具的配置文件，通过**符号链接（绝对路径）**部署到 `$HOME` 下对应位置（`~/.config/<tool>/` 等）。部署是**按机器选择性**的：仓库中的文件不一定全部链接到每台机器。

## 目录结构

| 路径 | 内容 |
|---|---|
| `.xonshrc` | xonsh shell 配置（pyenv / nvm / zvm / bun / 别名） |
| `.config/zellij/` | zellij 终端复用器配置（`config.kdl`，351 行重绑键位） |
| `.config/kitty/` | kitty 终端配置（`kitty.conf` + 主题 `catppuccin.conf` / `ir_black.conf`） |
| `.config/helix/` | helix 编辑器配置（极简，`ayu_evolve` 主题） |
| `.config/gitui/` | gitui 键位（`key_bindings.ron`） |
| `.config/lazyvim/` | LazyVim 插件配置（`lua/plugins/*.lua`） |
| `.config/nvim/` | nvim 用户配置（`lua/user/`，含 completion 配置） |
| `.agents/skills/` | 本机 agent 技能（如 `siyuan-flatpak`） |

每层配置目录下可能有自己的 `AGENTS.md`，管理该目录的规则以它为准。

## 规则

- 所有改动直接在仓库真实文件上进行并提交推送。`~/.config` 下的链接与真实文件是同一 inode，在那里编辑等价于在这里编辑，但容易忘记回仓库提交导致换机丢失——**不要**只留本地改动。
- 新增配置：文件放对应目录 → 建软链接 → 重启/重载目标工具验证。
- 配置必须机器可移植：不硬编码机器相关绝对路径、不放密钥；依赖外部工具或字体（如 kitty 的 `Maple Mono NF CN`、Nerd Font）时在注释中说明。
- 仓库路径若移动（如从 `~/Projects/dotfiles` 迁走），所有绝对路径软链接需重建。
- `.config/zellij/.gitignore` 忽略 `plugins/`（zellij 自行下载的插件目录，不入库）。

## 提交风格

沿用现有 conventional commits：`feat: ...` / `style: ...`（见 `git log`）。

