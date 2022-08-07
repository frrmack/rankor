
.PHONY: all install clean test run

all:
	@echo "install - Install all dependencies"
	@echo "clean   - Delete generated files"
	@echo "test    - Run tests"
	@echo "run     - Run development server"


test:
	python -m tests.run_all_tests


clean:
	rm -rf build dist *.egg-info .tox .pytest_cache pip-wheel-metadata .DS_Store
	find rankor -name '__pycache__' | xargs rm -rf
	find tests -name '__pycache__' | xargs rm -rf


install:
	python -m pip install -e .


run:
	FLASK_DEBUG=true FLASK_APP=rankor flask run
