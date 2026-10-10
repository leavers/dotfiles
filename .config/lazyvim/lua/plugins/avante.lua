return {
	{
		"yetone/avante.nvim",
		opts = {
			provider = "kimi",
			providers = {
				kimi = {
					endpoint = "https://api.moonshot.cn/v1",
					model = "kimi-k3",
					timeout = 30000, -- Timeout in milliseconds
					extra_request_body = {
						temperature = 0.75,
						max_tokens = 32768,
					},
				},
			},
		},
	},
}
