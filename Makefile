.PHONY: build upload install test test-all test-request test-filter

build:
	rm -rf dist/ build/
	python3 -m pip install build
	python3 -m build .

test:
	pytest -v -s ./test/test_filterMode_basic.py ./test/test_filterMode_advanced.py ./test/test_requestMode.py

test-request:
	pytest -v -s ./test/test_requestMode*.py

test-filter:
	pytest -v -s ./test/test_filterMode*.py

test-all:
	pytest -v -s ./test/*.py

upload:
	python3 -m pip install twine
	python3 -m twine upload dist/tulp-*
	rm -rf dist

install: 
	python3 -m pip install  --force-reinstall dist/tulp-*.tar.gz



