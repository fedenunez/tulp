# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TULP (TULP Understands Language Promptly) is a POSIX-inspired command-line tool for processing, filtering, and creating data using AI models. It pipes stdin to various LLM providers (OpenAI, Anthropic, DeepSeek, Z.ai, Gemini, Groq, Ollama) and outputs processed results to stdout, similar to `sed`, `awk`, or `jq`.

## Build and Development Commands

```bash
# Install in editable mode for development
pip install -e .

# Run all core tests
make test

# Run specific test suites
make test-filter    # Filter mode tests
make test-request   # Request mode tests
make test-all       # All tests including slow tests

# Build distribution
make build

# Lint (matches CI)
pylint $(git ls-files '*.py')
```

Tests use pytest and are located in `test/`. Test files follow the pattern `test_*.py`.

## Architecture

### Entry Points and Flow

1. **CLI Entry** (`tulp/cli.py`): `run()` function parses args, initializes config, selects mode, and dispatches to processing
2. **Mode Selection** determines which prompt factory and processor to use:
   - Standard processing: `core.process_request()` with `prompts/filtering.py` (stdin) or `prompts/request.py` (no stdin)
   - Code execution (`-x`): `executor.handle_execution_request()` with `prompts/program.py` or `prompts/filtering_program.py`

### LLM Provider System

`tulp/llms/` uses dynamic module loading:
- Modules must be named `Llm*.py` and export: `Client` class, `getArguments()`, `getModels()`
- `get_model_client(model_name, config)` matches model names via regex patterns to find the correct provider
- Currently supports: OpenAI (`gpt-*`, `chatgpt-*`, `openai.*`), Anthropic (`claude-*`), DeepSeek (`deepseek-*`), Z.ai (`glm-*`, `zai.*`), Gemini (`gemini*`), Groq (`groq.*`), Ollama (`ollama.*`)
- Provider modules must not import their SDK at module level (it costs seconds at startup): check with `sdk.is_installed()` and import on first `Client()` via `_import_sdk()`; `test_startup_does_not_import_provider_sdks` guards this
- `llms/openai_compat.py` and `llms/sdk.py` (no `Llm` prefix, so not loaded as providers) is the shared base `OpenAICompatClient` for OpenAI-compatible Chat Completions providers (DeepSeek, Z.ai)

### Response Format (Tag System)

LLM responses use a structured tag format defined in `tulp/constants.py`:
- Responses wrapped in `<|||reply_start|||>` and `<|||reply_end|||>`
- Content blocks: `<|||dev_file_start=stdout|||>`, `<|||dev_file_start=stderr|||>`, `<|||dev_file_start=error|||>`
- Block end: `<|||dev_file_end|||>`

`response_parser.py` parses this format; use helper functions: `parse_response()`, `has_reply_end()`, `block_exists()`, `block_content()`, `block_is_not_empty()`

### Configuration Hierarchy

Precedence: CLI args > Environment variables (`TULP_*` prefix) > Config file (`~/.tulp.conf`) > Defaults

Config is a singleton initialized via `initialize_config(args)` and accessed via `get_config()`.

## Key Files

- `tulp/constants.py`: Tag definitions, default values, block names
- `tulp/config.py`: Configuration singleton with `TulpConfig` class
- `tulp/prompts/`: Four prompt factories that generate messages for different modes
- `tulp/executor.py`: Handles `-x` mode (code generation and subprocess execution)
- `tulp/input_handler.py`: Stdin reading and chunking for large inputs
- `tulp/output_handler.py`: Stdout/stderr output and file writing
- `tulp/model_lister.py`: `--list-models`; queries every configured provider's `Client.list_models()` in parallel, maps ids to `-m` names, drops non-text models

## Testing

Tests invoke `tulp` as a subprocess via `test/utils.py:execute()`. When adding tests:
- Place in `test/test_*.py` following existing naming (filterMode, requestMode)
- Long-running or API-dependent tests go in `test_slowtest.py`
- Use `TULP_MODEL` env var to test against different providers

## Adding a New LLM Provider

1. Create `tulp/llms/Llm<Provider>.py`
2. Implement `Client` class with `__init__(self, config)`, `generate(self, messages)` and `list_models(self)` (raw provider ids for `--list-models`; set `MODEL_PREFIX` if ids need a prefix to route back, e.g. `groq.`)
3. Implement `getArguments()` returning list of arg dicts with `name`, `description`, `default`
4. Implement `getModels()` returning list of dicts with `idRe` (regex pattern) and `description`
5. The module will be auto-discovered on import

## Provider-Specific Notes

### Gemini (google-genai SDK)
- Uses `google-genai` package (NOT the deprecated `google-generativeai`)
- API: `client = genai.Client(api_key=...)`, then `client.models.generate_content(...)`
- Message format uses `types.Content` and `types.Part.from_text(text=...)` (keyword-only!)
- Thinking support via `types.ThinkingConfig(thinking_level='low'|'medium'|'high')` for Gemini 2.5+ (3.x, 4.x) models

### OpenAI
- Supports `gpt-*`, `chatgpt-*`, `o1-*`, `o3-*`, `codex-*` patterns; default model `gpt-6-luna`
- gpt-4.1+, GPT-5/6 (any `gpt-N` with N >= 5) and codex use the Responses API; GPT-5+ get `reasoning={"effort": <thinking level>}` (retried without it on a 400)
- o-series models (retiring 2026) use Chat Completions with `reasoning_effort`

### Anthropic
- Claude 4.6+, 5.x, Fable, Mythos: `thinking={"type": "adaptive"}` + `output_config={"effort": <thinking level>}` (budget_tokens is rejected on 4.7+)
- Older models: `thinking` with `budget_tokens` (low=2048, medium=4096, high=16000)
- Requests are streamed (`messages.stream` + `get_final_message`) because of the large `max_tokens`; never send `temperature`/`top_p`/`top_k`
- Has fallback retry without thinking if model doesn't support it

### DeepSeek / Z.ai (OpenAI-compatible, `openai` SDK)
- DeepSeek: base URL `https://api.deepseek.com`; `extra_body={"thinking": {"type": "enabled"}, "reasoning_effort": <thinking level>}`
- Z.ai: base URL `https://api.z.ai/api/paas/v4/` (Coding Plan: `https://api.z.ai/api/coding/paas/v4` via `zai_baseurl`); thinking on/off only, no effort control
- No `temperature`/`max_tokens` sent: thinking ignores sampling params and reasoning can exhaust a low `max_tokens`

## Development Notes

- Version is in `tulp/version.py` - update this when releasing
- On Ubuntu/Debian with system Python, use `pip install --user --break-system-packages -e .`
- Arguments use dashes in CLI (`--gemini-api-key`) but underscores internally (`gemini_api_key`)
- The `arguments.py` MODEL_HELP constant contains human-readable model list shown in `--help`; keep it, the README `tulp -h` block, and `setup.cfg` pins current when providers ship new models/SDKs
- Python 3.10+ (`X | None` annotations are evaluated at import)
