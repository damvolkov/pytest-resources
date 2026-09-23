##### CONFIG #####
PROJECT ?= pytest-resources
PACKAGE ?= src/pytest_resources
MODULE  ?= pytest_resources
ARGS     = $(filter-out $@,$(MAKECMDGOALS))

RESET   := \033[0m
BOLD    := \033[1m
GREEN   := \033[0;32m
CYAN    := \033[0;36m
GRAY    := \033[0;90m

SHELL := bash
.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory

##### TARGETS #####
.PHONY: help install sync lock lint format type arch validate test cov docs docs-build check ci release clean hooks

help:
	@printf "$(BOLD)$(CYAN)$(PROJECT)$(RESET) $(GRAY)· uv · ruff · ty · tach · pytest · e-serde · pytest plugin$(RESET)\n\n"
	@awk 'BEGIN{FS=":.*##"} /^[a-z][a-zA-Z0-9_-]*:.*##/{printf "  $(GREEN)%-8s$(RESET) $(GRAY)%s$(RESET)\n",$$1,$$2}' $(MAKEFILE_LIST)

# — env —
install: ## full setup: sync deps + git hooks
	@uv sync
	@uv run prek install
	@printf "$(GREEN)✓ ready$(RESET)\n"

sync: ## sync all deps (main + dev)
	@uv sync

lock: ## refresh uv lockfile
	@uv lock

# — gates —
lint: ## ruff check + format
	@uv run ruff check --fix $(PACKAGE) tests conftest.py
	@uv run ruff format $(PACKAGE) tests conftest.py

type: ## ty type check
	@uv run ty check

arch: ## enforce import architecture (tach)
	@uv run tach check

validate: ## validate pyproject.toml against schema
	@uv run validate-pyproject pyproject.toml

# — tests —
test: ## run tests [args: forwarded]
	@uv run pytest tests $(TESTARGS) -q

cov: ## run tests with coverage gate (fail under 90%)
	@uv run pytest tests --cov --cov-report=term-missing

# — docs —
docs: ## serve docs site live
	@uv run mkdocs serve

docs-build: ## strict docs build to site/
	@uv run mkdocs build --strict

# — aggregate —
check: lint type arch validate test ## fast local gate: lint + type + arch + validate + test
ci: lint type arch validate cov docs-build ## full pipeline: every gate CI runs, in one command

# — release —
release: ## build sdist + wheel into dist/
	@rm -rf dist
	@uv build
	@printf "$(GREEN)✓ built$(RESET)\n"

clean: ## remove build and cache artifacts
	@rm -rf dist .pytest_cache .ruff_cache .coverage site
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +

hooks: ## run all pre-commit hooks on every file
	@uv run prek run --all-files
