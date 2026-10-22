# llms/LlmDeepSeek.py
"""DeepSeek provider (OpenAI-compatible API: https://api-docs.deepseek.com/)."""
from typing import List, Dict, Any
from ..logger import log
from .openai_compat import OpenAICompatClient, OPENAI_AVAILABLE


def getModels() -> List[Dict[str, str]]:
    """Returns model definitions for DeepSeek."""
    if not OPENAI_AVAILABLE:
        log.warning("OpenAI library not found (required by DeepSeek). Install it with: pip install openai")
        return []
    return [{
        "idRe": r"deepseek-.*",
        "description": "Any DeepSeek model (e.g. deepseek-flash, deepseek-v4-pro; https://api-docs.deepseek.com/), requires DEEPSEEK_API_KEY",
    }]


def getArguments() -> List[Dict[str, Any]]:
    """Returns argument definitions specific to DeepSeek."""
    if not OPENAI_AVAILABLE:
        return []
    return [
        {"name": "deepseek_api_key", "description": "DeepSeek API key", "default": None},
        {"name": "deepseek_baseurl", "description": f"Override DeepSeek API base URL (default: {Client.DEFAULT_BASEURL})", "default": None},
    ]


class Client(OpenAICompatClient):
    """Client for DeepSeek models."""
    PROVIDER_NAME = "DeepSeek"
    API_KEY_ARG = "deepseek_api_key"
    BASEURL_ARG = "deepseek_baseurl"
    DEFAULT_BASEURL = "https://api.deepseek.com"
    MODELS_DOC_URL = "https://api-docs.deepseek.com/"
    API_KEY_URL = "https://platform.deepseek.com/api_keys"  # FIXME: unverified URL, confirm on deepseek.com

    def _extra_params(self, model_name: str) -> Dict[str, Any]:
        """
        Thinking mode: enabled via `thinking` (extra_body), depth via `reasoning_effort`.
        DeepSeek accepts low/medium/high and maps them itself (medium -> high).
        Both go in extra_body so older openai SDKs without a typed reasoning_effort still work.
        """
        extra_body: Dict[str, Any] = {"thinking": {"type": "enabled"}}
        if self.config.thinking_level:
            extra_body["reasoning_effort"] = self.config.thinking_level
        return {"extra_body": extra_body}
