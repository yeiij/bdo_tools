.PHONY: help install run build clean test

# Default target
help:
	@echo "Available commands:"
	@echo "  make install   - Install dependencies using uv"
	@echo "  make run       - Run the application"
	@echo "  make build     - Build the standalone executable"
	@echo "  make test      - Run tests"
	@echo "  make coverage  - Run tests with coverage report"
	@echo "  make clean     - Remove build artifacts and cache"

# Install dependencies
install:
	uv sync --extra dev

# Run the application
run:
	uv run python -m src.main

build:
	uv run python build_exe.py

# Run tests
test:
	uv run pytest tests

# Clean build artifacts
clean:
	rm -rf build dist *.spec
	rm -rf __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f .coverage
	rm -rf htmlcov

# Run coverage
coverage:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html tests
	@echo "HTML report generated in htmlcov/index.html"
