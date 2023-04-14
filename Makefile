.PHONY: build upload install test

build:
	rm -rf dist/ build/
	python3 -m pip install build
	python3 -m build .

test:
	pytest -v ./test/test_tulp.py
	TULP_MODEL=gpt-4 pytest -v ./test/test_tulp_only_gpt4.py

upload:
	python3 -m pip install twine
	python3 -m twine upload dist/tulp-*
	rm -rf dist

install: 
	python3 -m pip install  --force-reinstall dist/tulp-*.tar.gz



