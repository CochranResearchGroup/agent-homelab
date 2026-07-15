.PHONY: install test lint skills scan build inspect check

install:
	python -m pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check .

skills:
	python scripts/validate-skills.py

scan:
	scripts/scan-public.sh .

build:
	python -m build
	python scripts/package-skills.py

inspect: build
	python scripts/inspect-dist.py dist

check: lint test skills scan inspect
