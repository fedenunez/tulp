# llms/LlmZai.py
"""Z.ai (Zhipu GLM) provider (OpenAI-compatible API: https://docs.z.ai/)."""
from typing import List, Dict, Any
from ..logger import log
from .openai_compat import OpenAICompatClient, OPENAI_AVAILABLE


def getModels() -> List[Dict[str, str]]:
    """Returns model definitions for Z.ai."""
    if not OPENAI_AVAILABLE:
        log.warning("OpenAI library not found (required by Z.ai). Install it with: pip install openai")
        return []
    return [{
        "idRe": r"(glm-|zai\.).*",
        "description": "Any Z.ai GLM model (e.g. glm-5.3, glm-4.7; https://docs.z.ai/), or 'zai.<MODEL_ID>' for other ids. Requires ZAI_API_KEY",
    }]


def getArguments() -> List[Dict[str, Any]]:
    """Returns argument definitions specific to Z.ai."""
    if not OPENAI_AVAILABLE:
        return []
    return [
        {"name": "zai_api_key", "description": "Z.ai API key", "default": None},
        {"name": "zai_baseurl", "description": f"Override Z.ai API base URL (default: {Client.DEFAULT_BASEURL}; GLM Coding Plan: {Client.CODING_PLAN_BASEURL})", "default": None},
    ]


class Client(OpenAICompatClient):
    """Client for Z.ai GLM models."""
    PROVIDER_NAME = "Z.ai"
    API_KEY_ARG = "zai_api_key"
    BASEURL_ARG = "zai_baseurl"
    DEFAULT_BASEURL = "https://api.z.ai/api/paas/v4/"
    CODING_PLAN_BASEURL = "https://api.z.ai/api/coding/paas/v4"
    MODEL_PREFIX = "zai."
    MODELS_DOC_URL = "https://docs.z.ai/"
    API_KEY_URL = "https://z.ai/manage-apikey/apikey-list"  # FIXME: unverified URL, confirm on z.ai

    def _extra_params(self, model_name: str) -> Dict[str, Any]:
        """
        Thinking is on/off only (no effort control); it is the default on GLM-4.7+
        and cannot be disabled on GLM-5.3, so --thinking-level just enables it.
        """
        log.debug(f"Z.ai has no reasoning effort control: thinking enabled, --thinking-level '{self.config.thinking_level}' ignored.")
        return {"extra_body": {"thinking": {"type": "enabled"}}}
