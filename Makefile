.PHONY: build upload install

build:
	rm -rf dist/ build/
	python3 -m pip install build
	python3 -m build .

upload:
	python3 -m pip install twine
	python3 -m twine upload dist/tulp-*
	rm -rf dist

install: 
	python3 -m pip install  --force-reinstall dist/tulp-*.tar.gz



