help:
	@echo "make help     - Show this text"
	@echo "make dev      - Installs development requirements"
	@echo "make test     - Run tests"
	@echo "make test-all - Run all tests"

dev:
	pip install -e .

test:
	python setup.py test

test-all:
	tox

.PHONY: help test test-all
