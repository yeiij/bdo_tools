.PHONY: help install run build clean test lint format typecheck check-all checks ping-trace ping-summary

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
	@echo "  make typecheck - Run ty"
	@echo "  make ping-trace - Capture ping telemetry to ping_trace.jsonl"
	@echo "  make ping-summary - Summarize ping_trace.jsonl"
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
	uv run --extra dev pytest --no-cov tests/unit tests/integration tests/functional

# Run only unit tests (fast)
test-unit:
	uv run --extra dev pytest --no-cov tests/unit -v

# Run only integration tests
test-integration:
	uv run --extra dev pytest --no-cov tests/integration -v

# Run only functional tests
test-functional:
	uv run --extra dev pytest --no-cov tests/functional -v

# Clean build artifacts
clean:
	python -c "import pathlib, shutil; [shutil.rmtree(path, ignore_errors=True) for path in ('build','dist','htmlcov','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache')]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__') if p.is_dir()]; [p.unlink() for p in pathlib.Path('.').glob('*.spec') if p.is_file()]; cov=pathlib.Path('.coverage'); cov.unlink(missing_ok=True)"

# Run coverage
coverage:
	uv run --extra dev pytest --cov-report=html tests/unit tests/integration tests/functional
	@echo "HTML report generated in htmlcov/index.html"

# QA Tools
lint:
	uv run --extra dev ruff check src main.py

format:
	uv run --extra dev ruff format src main.py

typecheck:
	uv run --extra dev ty check src main.py

ping-trace:
	uv run --extra dev python scripts/ping_trace.py --duration 60 --interval 2 --output ping_trace.jsonl

ping-summary:
	uv run --extra dev python scripts/ping_trace.py --summary ping_trace.jsonl

check-all: lint typecheck test

checks: check-all
