# Repository Guidelines

## Project Structure & Module Organization
`tulp/` holds the CLI entry (`cli.py`), shared orchestration code (`core.py`, `executor.py`) and feature packages (`llms/`, `prompts/`, `input_handler.py`, `response_parser.py`). Place new runtime assets beside their closest module to avoid broad imports. Tests live in `test/`, mirroring feature groupings (`test_filterMode_*`, `test_requestMode.py`), while `examples/` contains user-facing samples. Build artifacts are written to `dist/`; keep the directory clean in commits.

## Build, Test, and Development Commands
- `pip install -e .` installs TULP in editable mode for local iteration.
- `make test` or `pytest -v -s ./test` runs the core request and filter suites; prefer `make test-filter` or `make test-request` for targeted loops.
- `make build` regenerates wheels and source dists via `python -m build`, clearing `dist/` beforehand.
- `pylint $(git ls-files '*.py')` matches the CI workflow; ensure a clean report before pushing.

## Coding Style & Naming Conventions
Follow standard PEP 8 with 4-space indents, module-level constants in `UPPER_SNAKE_CASE`, and runtime helpers in `lower_snake_case`. Keep CLI-visible strings centralized in `constants.py` or `prompts/` to maintain translation parity. Prefer explicit imports within the relevant submodule to avoid cyclical dependencies, and add short docstrings when exposing new public functions.

## Testing Guidelines
Pytest powers the suite; new tests should land in `test/` using the `test_*` naming convention and rely on fixtures in `test/utils.py`. Replicate the structure of existing filter/request tests so behavior-focused cases stay easy to trace. Long-running scenarios belong in `test/test_slowtest.py`; gate them behind markers or environment checks if they require external APIs.

## Commit & Pull Request Guidelines
Commits typically use concise, imperative subjects with optional type prefixes (`feat:`, `Refactor:`) as seen in recent history. Keep each commit focused, staged after `make test` and `pylint`. Pull requests should summarize the change, list validation steps, link any tracking issue, and attach CLI transcripts or screenshots when adjusting user-facing flows.

## Configuration & Security Tips
TULP consumes provider credentials via environment variables or `tulpconfig.py`; never commit real keys. When adding new configuration knobs, document the `TULP_`-prefixed env var in `README.md` and ensure defaults land in `config.py`. Review generated Python in `-x` execution paths for safety, especially when expanding executor capabilities.

## Documentation
Treat `README.md` as a pure user manual: highlight installation, usage, and visible changes only. Keep implementation notes, architecture history, and contributor workflows in `AGENTS.md` or developer changelogs so the README stays concise and user-focused.
