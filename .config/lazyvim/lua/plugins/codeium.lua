return {
	"Exafunction/codeium.vim",
	event = "BufEnter",
	config = function()
		-- 默认键位（插入模式）
		-- <Tab> 接受建议
		-- <C-]> 下一个建议
		-- <C-[> 上一个建议
		-- <C-x> 拒绝/清除当前建议

		-- -- 禁用默认键位绑定
		-- vim.g.codeium_disable_bindings = 1

		-- -- 自定义键位绑定
		-- vim.keymap.set("i", "<C-g>", function()
		-- 	return vim.fn["codeium#Accept"]()
		-- end, { expr = true, silent = true })
		-- vim.keymap.set("i", "<C-;>", function()
		-- 	return vim.fn["codeium#CycleCompletions"](1)
		-- end, { expr = true, silent = true })
		-- vim.keymap.set("i", "<C-,>", function()
		-- 	return vim.fn["codeium#CycleCompletions"](-1)
		-- end, { expr = true, silent = true })
		-- vim.keymap.set("i", "<C-x>", function()
		-- 	return vim.fn["codeium#Clear"]()
		-- end, { expr = true, silent = true })

		-- 可选：设置状态显示
		-- vim.g.codeium_enabled = true
	end,
}
