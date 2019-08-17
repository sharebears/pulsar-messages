lint:
	isort -rc .
	black -S -t py37 -l 79 .

tests:
	flake8
	mypy --no-strict-optional messages/
	pytest --cov-report term-missing --cov-branch --cov=messages tests/

.PHONY: lint tests
