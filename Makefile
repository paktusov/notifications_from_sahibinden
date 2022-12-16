APPLICATION_NAME_1 = app
APPLICATION_NAME_2 = telegram


env:  ##@Environment Create .env file with variables
	@$(eval SHELL:=/bin/bash)
	@cp .env.sample .env

lint:  ##@Code Check code with pylint
	poetry run python3 -m pylint $(APPLICATION_NAME_1)
	poetry run python3 -m pylint $(APPLICATION_NAME_2)

format:  ##@Code Reformat code with isort and black
	poetry run python3 -m isort $(APPLICATION_NAME_1)
	poetry run python3 -m black $(APPLICATION_NAME_1)
	poetry run python3 -m isort $(APPLICATION_NAME_2)
	poetry run python3 -m black $(APPLICATION_NAME_2)