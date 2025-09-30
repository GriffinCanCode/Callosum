.PHONY: help build-core build-python test-core test-python clean install dev

# Default target
help:
	@echo "Callosum Development Commands:"
	@echo "  help          Show this help message"
	@echo "  build-core    Build OCaml DSL compiler"
	@echo "  build-python  Build Python package"
	@echo "  build         Build both core and python"
	@echo "  test-core     Run OCaml tests"
	@echo "  test-python   Run Python tests"
	@echo "  test          Run all tests"
	@echo "  clean         Clean all build artifacts"
	@echo "  install       Install Python package for development"
	@echo "  dev           Setup development environment"

# Core DSL Compiler (OCaml)
build-core:
	cd core && dune build

test-core:
	cd core && dune runtest

# Python Package
build-python: build-core
	cd python && python3 -m build

test-python:
	cd python && python3 -m pytest tests/

install:
	cd python && pip install -e .

# Combined targets
build: build-core build-python

test: test-core test-python

# Clean up
clean:
	cd core && dune clean
	cd python && rm -rf build/ dist/ *.egg-info/
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Development setup
dev: clean build install
	@echo "Development environment ready!"
	@echo "Try: callosum-compile --help"
