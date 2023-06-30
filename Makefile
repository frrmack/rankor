
.PHONY: all install clean test rundev run


all:
	@echo "install - Install all dependencies"
	@echo "clean   - Delete generated files"
	@echo "test    - Run tests"
	@echo "rundev  - Run development server"
	@echo "run     - Run production server"


install:
	python3 -m pip install -Ue .


clean:
	rm -rf rankor/*.egg-info pip-wheel-metadata
	find . -name '__pycache__' | xargs rm -rf
	find . -name '.pytest_cache' | xargs rm -rf
	find . -name '.DS_Store' | xargs rm -rf


test:
	python3 -m pytest


rundev:
	FLASK_DEBUG=true FLASK_APP=rankor flask run


run:
	gunicorn --bind 0.0.0.0:5000 rankor:app -w 4