help:
	@echo "make help          - Show this text"
	@echo "make dev           - Installs development requirements"
	@echo "make test          - Run tests"
	@echo "make test-all      - Run all tests"
	@echo "make coverage      - Create coverage data"
	@echo "make view-coverage - View coverage data"
	@echo "make docs          - Build the HTML documentation"
	@echo "make view-docs     - View the HTML documentation"

dev:
	pip install -e .
	pip install pytest-cov

test:
	python setup.py test

test-all:
	tox

coverage:
	py.test --cov=flask_relief --cov=test_flask_relief.py
	coverage html

view-coverage: coverage
	open htmlcov/index.html

docs:
	make -C docs html

view-docs: docs
	open docs/_build/html/index.html

.PHONY: help dev test test-all coverage view-coverage docs view-docs
