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

test-models:
	RES_DIR="$(shell mktemp -d res-$$(date +%Y-%m-%d_%H:%M)-XXX)"; \
	TULP_MODEL=gpt-4o                   pytest -v -s | tee $$RES_DIR/$${TULP_MODEL}.log  ;\
	TULP_MODEL=gpt-4-turbo              pytest -v -s | tee $$RES_DIR/$${TULP_MODEL}.log  ;\
	TULP_MODEL=gpt-3.5-turbo            pytest -v -s | tee $$RES_DIR/$${TULP_MODEL}.log  ;\
	TULP_MODEL=claude-3-opus-20240229   pytest -v -s | tee $$RES_DIR/$${TULP_MODEL}.log  ;\
	TULP_MODEL=gemini-1.5-pro-latest    pytest -v -s | tee $$RES_DIR/$${TULP_MODEL}.log  ;\
	TULP_MODEL=groq.gemma-7b-it   tell  pytest -v -s | tee $$RES_DIR/$${TULP_MODEL}.log  ;\
	TULP_MODEL=groq.llama3-70b-8192     pytest -v -s | tee $$RES_DIR/$${TULP_MODEL}.log  ;\
	TULP_MODEL=groq.mixtral-8x7b-32768  pytest -v -s | tee $$RES_DIR/$${TULP_MODEL}.log  ;\
	TULP_MODEL=ollama.phi3:instruct     pytest -v -s | tee $$RES_DIR/$${TULP_MODEL}.log  

upload:
	python3 -m pip install twine
	python3 -m twine upload dist/tulp-*
	rm -rf dist

install: 
	python3 -m pip install  --force-reinstall dist/tulp-*.tar.gz



