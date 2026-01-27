.PHONY: help install run build clean test lint format typecheck check-all

# Default target
help:
	@echo "Available commands:"
	@echo "  make install   - Install dependencies using uv"
	@echo "  make run       - Run the application"
	@echo "  make build     - Build the standalone executable"
	@echo "  make test      - Run tests"
	@echo "  make coverage  - Run tests with coverage report"
	@echo "  make lint      - Run ruff check"
	@echo "  make format    - Run ruff format"
	@echo "  make typecheck - Run mypy"
	@echo "  make check-all - Run all QA tools"
	@echo "  make clean     - Remove build artifacts and cache"

# Install dependencies
install:
	uv sync --extra dev

# Run the application
run:
	uv run python main.py

build:
	uv run python build_exe.py

# Run tests
test:
	uv run pytest tests/unit tests/integration tests/functional

# Run only unit tests (fast)
test-unit:
	uv run pytest tests/unit -v

# Run only integration tests
test-integration:
	uv run pytest tests/integration -v

# Run only functional tests
test-functional:
	uv run pytest tests/functional -v

# Clean build artifacts
clean:
	rm -rf build dist *.spec
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f .coverage
	rm -rf htmlcov

# Run coverage
coverage:
	uv run pytest --cov=src --cov-config=coverage.toml --cov-report=term-missing --cov-report=html tests/unit tests/integration tests/functional
	@echo "HTML report generated in htmlcov/index.html"

# QA Tools
lint:
	uv run ruff check src main.py

format:
	uv run ruff format src main.py

typecheck:
	uv run mypy src main.py

check-all: lint typecheck test
