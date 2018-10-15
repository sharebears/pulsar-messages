lint:
	isort -rc .
_tests:
	flake8
	mypy --no-strict-optional messages/
	pytest --cov-report term-missing --cov-branch --cov=messages tests/
tests: _tests
