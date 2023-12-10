local custom = {}

custom["Vimjas/vim-python-pep8-indent"] = {
	lazy = true,
	event = "BufRead",
	ft = "python",
}
custom["dasupradyumna/midnight.nvim"] = {
	lazy = false,
}

return custom
