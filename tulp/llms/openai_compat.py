# llms/openai_compat.py
"""
Shared client for providers exposing an OpenAI-compatible Chat Completions API
(DeepSeek, Z.ai, ...).

Not named Llm*.py on purpose: it is a helper, not a provider module, so the
dynamic loader in llms/__init__.py skips it.
"""
from typing import List, Dict, Any, Optional
from ..logger import log
from ..config import TulpConfig
from .. import constants

from .sdk import is_installed

# The SDK is imported on first Client() (see llms/sdk.py); these names are bound then.
OPENAI_AVAILABLE = is_installed("openai")
OpenAI = APIConnectionError = APIStatusError = RateLimitError = AuthenticationError = NotFoundError = None


def _import_sdk():
    """Imports the openai SDK into this module's globals (once)."""
    global OpenAI, APIConnectionError, APIStatusError, RateLimitError, AuthenticationError, NotFoundError  # pylint: disable=global-statement
    if OpenAI is None:
        from openai import OpenAI, APIConnectionError, APIStatusError, RateLimitError, AuthenticationError, NotFoundError  # pylint: disable=import-outside-toplevel,redefined-outer-name


class OpenAICompatClient:
    """
    Base client for OpenAI-compatible Chat Completions providers.

    Subclasses set the class attributes and may override `_extra_params()` to add
    provider-specific request parameters (e.g. thinking configuration).
    """
    PROVIDER_NAME = "OpenAI-compatible"   # Human-readable name for logs/errors
    API_KEY_ARG = ""                      # Argument name holding the API key (e.g. "deepseek_api_key")
    BASEURL_ARG = ""                      # Argument name holding the base URL override
    DEFAULT_BASEURL = ""                  # Base URL used when no override is configured
    MODEL_PREFIX = ""                     # Optional tulp-side prefix stripped from the model name (e.g. "zai.")
    API_KEY_URL = ""                      # Where users can get an API key
    MODELS_DOC_URL = ""                   # Where the provider documents its model ids

    def __init__(self, config: TulpConfig):
        self.config = config
        if not OPENAI_AVAILABLE:
            raise ImportError(f"OpenAI library is not installed (required by {self.PROVIDER_NAME}). Install it with: pip install openai")
        _import_sdk()

        api_key = config.get_llm_argument(self.API_KEY_ARG)
        if not api_key:
            log.error(f'{self.PROVIDER_NAME} API key not found. Please set the {constants.ENV_VAR_PREFIX}{self.API_KEY_ARG.upper()} environment variable, add it to {config.config_file_path}, or use --{self.API_KEY_ARG.replace("_", "-")}.')
            if self.API_KEY_URL:
                log.error(f"Get an API key at: {self.API_KEY_URL}")
            raise ValueError(f"{self.PROVIDER_NAME} API key is missing.")

        base_url = config.get_llm_argument(self.BASEURL_ARG) or self.DEFAULT_BASEURL
        try:
            assert OpenAI is not None
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            log.info(f"{self.PROVIDER_NAME} client initialized (base URL: {base_url}).")
        except Exception as e:
            log.error(f"Failed to initialize {self.PROVIDER_NAME} client: {e}")
            raise ValueError(f"{self.PROVIDER_NAME} client initialization failed: {e}") from e

    def list_models(self) -> List[str]:
        """Model ids from the provider's /models endpoint (for --list-models)."""
        try:
            return [m.id for m in self.client.with_options(timeout=constants.LIST_MODELS_TIMEOUT).models.list()]
        except NotFoundError as e:
            raise RuntimeError(f"{self.PROVIDER_NAME} has no model-listing endpoint at this base URL; "
                               f"see {self.MODELS_DOC_URL}") from e

    def _get_model_name(self) -> str:
        """Strips the tulp-side model prefix, if any."""
        model_name = self.config.model
        if self.MODEL_PREFIX and model_name.startswith(self.MODEL_PREFIX):
            model_name = model_name[len(self.MODEL_PREFIX):]
        return model_name

    def _extra_params(self, model_name: str) -> Dict[str, Any]:
        """Provider-specific parameters merged into the request. Override in subclasses."""
        return {}

    @staticmethod
    def _clean_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Keeps only role/content: core.py's continuation path appends whole response
        dicts (with finish_reason), which strict servers reject.
        """
        return [{"role": m.get("role", "user"), "content": m.get("content", "") or ""} for m in messages]

    def generate(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates a response through the Chat Completions endpoint."""
        model_name = self._get_model_name()
        params: Dict[str, Any] = {
            "model": model_name,
            "messages": self._clean_messages(messages),
        }
        # No temperature/top_p/max_tokens: thinking models ignore or constrain sampling
        # params, and a low max_tokens can be fully consumed by reasoning.
        params.update(self._extra_params(model_name))
        log.debug(f"Sending request to {self.PROVIDER_NAME} model: {model_name} (extra params: { {k: v for k, v in params.items() if k not in ('model', 'messages')} })")

        try:
            api_response = self.client.chat.completions.create(**params)
            log.debug(f"{self.PROVIDER_NAME} raw response object: {api_response}")
        except Exception as e:  # pylint: disable=broad-except
            return self._handle_exception(e, model_name)

        if not api_response.choices:
            log.error(f"{self.PROVIDER_NAME} response contained no choices.")
            return {"role": "error", "content": f"{self.PROVIDER_NAME} returned no choices.", "finish_reason": "error"}

        choice = api_response.choices[0]
        response_content: Optional[str] = getattr(choice.message, "content", None) or ""
        finish_reason = getattr(choice, "finish_reason", None) or "unknown"
        log.debug(f"{self.PROVIDER_NAME} finish reason: {finish_reason}")

        if finish_reason in ("content_filter", "sensitive"):
            log.error(f"{self.PROVIDER_NAME} response stopped by its content filter.")
            return {"role": "error", "content": f"Blocked by {self.PROVIDER_NAME} content filter", "finish_reason": "content_filter"}
        if finish_reason == "length":
            if not response_content:
                log.error(f"{self.PROVIDER_NAME} used the whole output budget on reasoning and returned no content.")
                return {"role": "error", "content": f"{self.PROVIDER_NAME} returned no content (output limit reached while reasoning). Try a lower --thinking-level.", "finish_reason": "length"}
            log.warning(f"{self.PROVIDER_NAME} response truncated due to length limit.")

        return {
            "role": getattr(choice.message, "role", None) or "assistant",
            "content": response_content,
            "finish_reason": finish_reason,
        }

    def _handle_exception(self, exception: Exception, model_name: str) -> Dict[str, Any]:
        """Maps SDK exceptions to tulp error responses."""
        name = self.PROVIDER_NAME
        if AuthenticationError is not None and isinstance(exception, AuthenticationError):
            log.error(f"{name} authentication error: {exception}. Check your API key.")
            return {"role": "error", "content": f"{name} Auth Error: {exception}", "finish_reason": "error"}
        if NotFoundError is not None and isinstance(exception, NotFoundError):
            log.error(f"{name} not found error: {exception}. Check model name ('{model_name}') or base URL.")
            return {"role": "error", "content": f"{name} Not Found Error: {exception}", "finish_reason": "error"}
        if RateLimitError is not None and isinstance(exception, RateLimitError):
            log.error(f"{name} rate limit exceeded (or insufficient balance): {exception}")
            return {"role": "error", "content": f"{name} Rate Limit Exceeded: {exception}", "finish_reason": "rate_limit"}
        if APIStatusError is not None and isinstance(exception, APIStatusError):
            message = getattr(exception, "message", str(exception))
            log.error(f"{name} API status error: {exception.status_code} - {message}")
            return {"role": "error", "content": f"{name} API Error ({exception.status_code}): {message}", "finish_reason": "error"}
        if APIConnectionError is not None and isinstance(exception, APIConnectionError):
            log.error(f"{name} API connection error: {exception}")
            return {"role": "error", "content": f"{name} Connection Error: {exception}", "finish_reason": "error"}
        log.error(f"Unexpected error during {name} generation: {exception}")
        import traceback
        log.debug(traceback.format_exc())
        return {"role": "error", "content": f"Unexpected Error: {exception}", "finish_reason": "error"}
