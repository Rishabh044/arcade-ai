VERSION ?= "0.1.1"

.PHONY: install
install: ## Install the poetry environment and install the pre-commit hooks
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "🚫 Poetry is not installed. Please install poetry before proceeding."; \
		exit 1; \
	fi
	@echo "🚀 Creating virtual environment using pyenv and poetry"
	@poetry install --all-extras
	@poetry run pre-commit install

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking Poetry lock file consistency with 'pyproject.toml': Running poetry check --lock"
	@poetry check --lock
	@echo "🚀 Linting code: Running pre-commit"
	@poetry run pre-commit run -a
	@echo "🚀 Static type checking: Running mypy"
	@poetry run mypy $(git ls-files '*.py')

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@poetry run pytest -W ignore -v --cov --cov-config=pyproject.toml --cov-report=xml

.PHONY: set-version
set-version: ## Set the version in the pyproject.toml file
	@echo "🚀 Setting version in pyproject.toml"
	@poetry version $(VERSION)

.PHONY: unset-version
unset-version: ## Set the version in the pyproject.toml file
	@echo "🚀 Setting version in pyproject.toml"
	@poetry version 0.1.0

.PHONY: build
build: clean-build ## Build wheel file using poetry
	@echo "🚀 Creating wheel file"
	@poetry build

.PHONY: clean-build
clean-build: ## clean build artifacts
	@rm -rf dist

.PHONY: publish
publish: ## publish a release to pypi.
	@echo "🚀 Publishing: Dry run."
	@poetry config pypi-token.pypi $(PYPI_TOKEN)
	@poetry publish --dry-run
	@echo "🚀 Publishing."
	@poetry publish

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: help
help:
	@echo "🛠️ Arcade AI Dev Commands:\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
