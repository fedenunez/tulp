.PHONY: build upload install test testall

build:
	rm -rf dist/ build/
	python3 -m pip install build
	python3 -m build .

test:
	pytest -v -s ./test/test_basic*.py ./test/test_advance*.py

testall:
	pytest -v -s ./test/*.py

upload:
	python3 -m pip install twine
	python3 -m twine upload dist/tulp-*
	rm -rf dist

install: 
	python3 -m pip install  --force-reinstall dist/tulp-*.tar.gz



