CODE = app bot

env:
	@$(eval SHELL:=/bin/bash)
	@cp .env.sample .env

lint:
	pylint $(CODE)

format:
	isort $(CODE)
	black $(CODE)