
.PHONY: all install clean test run


all:
	@echo "install - Install all dependencies"
	@echo "clean   - Delete generated files"
	@echo "test    - Run tests"
	@echo "rundev  - Run development server"
	@echo "run     - Run production server"


test:
	python -m tests.run_all_tests


clean:
	rm -rf rankor/*.egg-info tests/.pytest_cache pip-wheel-metadata .DS_Store rankor/.DS_Store
	find rankor -name '__pycache__' | xargs rm -rf
	find tests -name '__pycache__' | xargs rm -rf


install:
	python -m pip install -e .


rundev:
	FLASK_DEBUG=true FLASK_APP=rankor flask run


run:
	gunicorn --bind 0.0.0.0:5000 rankor:app -w 4