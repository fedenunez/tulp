# llms/sdk.py
"""
Cheap SDK availability checks.

Provider SDKs take seconds to import (anthropic ~1.5s, google-genai ~1.2s, openai ~1s), so
provider modules only check that their SDK is installed at load time and import it on the
first Client(): `tulp -h` and a run with one provider don't pay for all the others.
Not named Llm*.py, so the provider loader skips it.
"""
import importlib.util


def is_installed(module_name: str) -> bool:
    """True if `module_name` can be imported, without importing it."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):  # Missing parent package (e.g. 'google' for 'google.genai')
        return False
