-- 中文（CJK）不参与拼写检查，英文拼写检查保留
-- 覆盖 LazyVim 默认：lazyvim/config/options.lua -> opt.spelllang = { "en" }
vim.opt.spelllang = { "en", "cjk" }

return {}
