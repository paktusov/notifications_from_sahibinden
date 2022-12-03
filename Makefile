env:  ##@Environment Create .env file with variables
	@$(eval SHELL:=/bin/bash)
	@cp .env.sample .env