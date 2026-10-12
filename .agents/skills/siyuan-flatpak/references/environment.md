# 环境：Flatpak 沙箱下的 SiYuan

## 症状与根因

`siyuan --help`（`~/.local/bin/siyuan` → `flatpak run --command=.../SiYuan-Kernel org.b3log.siyuan "$@"`）会失败：

```text
error: Unable to allocate instance id
```

排查结论（已验证）：

- 失败发生在 flatpak 自身，应用还没启动：`flatpak run org.b3log.siyuan --version` 同样报错。
- 根因是它无法创建私有 instance 目录：`/run/user/1000/.flatpak` 是只读文件系统（`touch` 报 `Read-only file system`）。
- 影响所有 flatpak 应用，不只是 SiYuan。

## 挂载与可写性（决定「能用哪种手段改笔记」）

| 路径 | 状态 | 结论 |
| --- | --- | --- |
| `/`、`/home` | `btrfs ro,...` | 只读挂载，`sudo` 也不可用（no-new-privileges）；Reasonix 无法写 `~/.agents`、`~/.local`、`~/.var` 等 |
| `<workspace>`（本仓库） | `btrfs rw,...`（单独挂载点） | 可读写，临时脚本放这里的 `.reasonix-scratch/`，用完删除 |
| `/home/gaochang/Documents/SiYuan`（笔记工作区） | 位于 ro 的 `/home` 下 | **只能通过 HTTP API 改笔记**，不能直接改 `.sy` 文件 |
| `/tmp`、`/run/user/1000` | 部分只读 | `/tmp` 可写但 bash 与 Reasonix 文件工具的视图可能不同视图 |

## 三种可用手段（按推荐顺序）

### 1. 内核 HTTP API（首选）

GUI 运行时内核监听在本机端口（本机为 40111）：

```bash
ps -eo pid,args | grep -o 'SiYuan-Kernel serve --port [0-9]*' | head -1
```

拿到端口后即可 `curl`/`python urllib` 调用，详见 `http-api.md`。这是唯一被推荐的写入通道。

### 2. 直接执行 flatpak 部署里的内核二进制（只读子命令）

内核二进制在部署目录里，可以直接运行（绕过 flatpak 包装）：

```bash
K=/var/lib/flatpak/app/org.b3log.siyuan/current/active/files/siyuan/resources/kernel/SiYuan-Kernel
"$K" --help            # 完整的 CLI 命令树
"$K" workspace list    # 已注册的工作区（本机输出 /home/gaochang/Documents/SiYuan）
```

- 安全的子命令：`--help`、`version`、`workspace list`（只读，不碰工作区）。
- **不要**用它执行 `serve`，也不要对正在被 GUI 打开的工作区执行写操作（`sql` 写语句、`import`、`repo checkout` 等）——会和 GUI 的内核抢锁。
- 该二进制的版本即当前安装版本（本机 v3.8.6）。

### 3. 不要做的事

- 不要 `flatpak run ...`：见上，起不来。
- 不要 `SiYuan-Kernel serve -w <workspace>`：会打开第二个实例抢工作区锁。
- 不要直接编辑 `Documents/SiYuan/data/**/*.sy`：`/home` 只读，而且内核索引不会跟着更新。

## 版本核对

```bash
"$K" version                        # 或 curl /api/system/version
git -C <siyuan 源码仓库> describe --tags   # 本机源码仓库为 v3.8.6，与安装版一致
```

版本不一致时，CLI 子命令与 API 行为可能有差异，以运行中的内核为准。

## 环境变量速查

| 变量 | 用途 |
| --- | --- |
| `SIYUAN_API` | 覆盖内核 base URL（默认 `http://127.0.0.1:<探测到的端口>`） |
| `SIYUAN_TOKEN` | API token（写操作需要；不要落盘、不要写进回答） |
| `SIYUAN_WORKSPACE` | 覆盖笔记工作区路径（用于读 `conf/conf.json`） |
