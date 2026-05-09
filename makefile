PY_SRCS=src tests

.PHONY: help lint fmt test check

help:
	@echo "Доступные цели:"
	@echo " lint  - ruff check"
	@echo " fmt   - ruff format"
	@echo " test  - pytest"
	@echo " check - lint + format + test"

lint:
	uv run ruff check $(PY_SRCS) --fix

fmt:
	uv run ruff format $(PY_SRCS)

test:
	uv run pytest

check: lint fmt test
