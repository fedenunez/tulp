.PHONY: venv build test test-request test-filter test-all test-models testpackage upload install

VENV ?= .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

venv: $(PYTHON)

$(PYTHON):
	python3 -m venv --system-site-packages $(VENV)
	$(PYTHON) -m ensurepip --upgrade >/dev/null 2>&1 || true

build: venv
	rm -rf dist/ build/
	if ! $(PYTHON) -m pip show wheel >/dev/null 2>&1; then \
		$(PYTHON) -m pip install wheel >/dev/null 2>&1 || true; \
	fi
	$(PYTHON) setup.py sdist bdist_wheel || $(PYTHON) setup.py sdist

test: venv
	$(PYTHON) -m pytest -v -s ./test/test_filterMode_basic.py ./test/test_filterMode_advanced.py ./test/test_requestMode.py ./test/test_providers.py

test-request: venv
	$(PYTHON) -m pytest -v -s ./test/test_requestMode*.py

test-filter: venv
	$(PYTHON) -m pytest -v -s ./test/test_filterMode*.py

test-all: venv
	$(PYTHON) -m pytest -v -s ./test/*.py

test-models: venv
	RES_DIR="$$(mktemp -d res-$$(date +%Y-%m-%d_%H:%M)-XXX)"; \
	for MODEL in gpt-5-mini gpt-4o gpt-4-turbo gpt-3.5-turbo claude-3-opus-20240229 gemini-1.5-pro-latest groq.gemma-7b-it groq.llama3-70b-8192 groq.mixtral-8x7b-32768 ollama.phi3:instruct; do \
		echo "Running pytest with $$MODEL"; \
		TULP_MODEL=$$MODEL $(PYTHON) -m pytest -v -s | tee $$RES_DIR/$$MODEL.log; \
	done

testpackage: build
	docker run -t -i -v $(shell pwd):/tulp -w /tulp python python -m pip install dist/tulp-*.tar.gz

upload: testpackage
	$(PYTHON) -m pip install twine
	$(PYTHON) -m twine upload dist/tulp-*
	rm -rf dist

install: build
	$(PYTHON) -m pip install --force-reinstall dist/tulp-*.tar.gz
