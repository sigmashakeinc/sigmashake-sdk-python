.PHONY: docs test lint

docs:
	sphinx-build -b html docs docs/_build/html

test:
	pytest

lint:
	python -m mypy src/
