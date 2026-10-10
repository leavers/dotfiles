-- Python LSP 微调
-- 背景：mason 里装了 python-lsp-server（pylsp），LazyVim 通过 mason-lspconfig 的
-- automatic_enable 自动启用了它。pylsp 内置的 pycodestyle 插件有自己的默认
-- max-line-length=79，不读项目 pyproject.toml 里的 [tool.ruff] line-length=100，
-- 因此编辑器里出现的 "pycodestyle: E501 line too long (xx > 79 characters)"
-- 与 ruff 配置无关（当时 ruff LSP 甚至没在运行）。
-- 项目统一用 ruff 做风格检查，这里直接关闭 pylsp 的 pycodestyle 插件。
-- 若仍想保留 pycodestyle，可改为 { maxLineLength = 100 }。
return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        pylsp = {
          settings = {
            pylsp = {
              plugins = {
                pycodestyle = { enabled = false },
              },
            },
          },
        },
      },
    },
  },
}
