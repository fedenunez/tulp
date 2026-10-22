# tulp/llms/LlmAnthropic.py
import re
from typing import List, Dict, Any, Tuple, Optional
from ..logger import log
from ..config import TulpConfig
from .. import constants

from .sdk import is_installed

# The SDK is imported on first Client() (see llms/sdk.py); `anthropic` is bound then.
ANTHROPIC_AVAILABLE = is_installed("anthropic")
anthropic = None


def _import_sdk():
    """Imports the anthropic SDK into this module's globals (once)."""
    global anthropic  # pylint: disable=global-statement
    if anthropic is None:
        import anthropic  # pylint: disable=import-outside-toplevel,redefined-outer-name

def getModels() -> List[Dict[str, str]]:
   """Returns model definitions for Anthropic."""
   if not ANTHROPIC_AVAILABLE:
        return []
   # Use raw string r"" for regex patterns
   return [ { "idRe": r"claude-.*", "description": "Any Anthropic Claude model (e.g. claude-opus-5-5, claude-sonnet-5-5; https://platform.claude.com/docs/en/about-claude/models/overview), requires ANTHROPIC_API_KEY"} ]

def getArguments() -> List[Dict[str, Any]]:
   """Returns argument definitions specific to Anthropic."""
   if not ANTHROPIC_AVAILABLE:
       return []
   return [{"name": "anthropic_api_key", "description": "Anthropic API key", "default": None}]


class Client:
    """Client for interacting with Anthropic's Claude models."""
    MAX_TOKENS = 64000  # Adaptive-thinking models: shared by thinking and output; streaming keeps it clear of HTTP timeouts
    LEGACY_MAX_TOKENS = 4096  # Older models (some cap output at 4096); budget_tokens is added on top when thinking
    def __init__(self, config: TulpConfig):
        """Initializes the Anthropic client."""
        self.config = config
        if not ANTHROPIC_AVAILABLE:
             raise ImportError("Anthropic library is not installed. Cannot use Anthropic client.")
        _import_sdk()

        api_key = config.get_llm_argument("anthropic_api_key")
        if not api_key:
            log.error(f'Anthropic API key not found. Please set the {constants.ENV_VAR_PREFIX}ANTHROPIC_API_KEY environment variable, add it to {config.config_file_path}, or use --anthropic_api_key.')
            log.error("If you don't have one, please create one at: https://console.anthropic.com")
            raise ValueError("Anthropic API key is missing.")
        try:
            assert anthropic is not None
            self.client = anthropic.Anthropic(api_key=api_key)
            log.info("Anthropic client initialized.")
        except Exception as e:
            log.error(f"Failed to initialize Anthropic client: {e}")
            raise

    def list_models(self) -> List[str]:
        """Model ids available to this API key (for --list-models)."""
        return [m.id for m in self.client.with_options(timeout=constants.LIST_MODELS_TIMEOUT).models.list()]

    def _convert_messages(self, messages: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        Converts OpenAI message format to Anthropic format.
        """
        if not messages:
            return [], None

        anthropic_messages = []
        system_prompt: Optional[str] = None
        openai_msgs_to_convert = messages

        # Extract system prompt if it's the first message
        if messages[0]['role'] == 'system':
            system_prompt = messages[0]['content']
            openai_msgs_to_convert = messages[1:]
            log.debug("Using first message as Anthropic system prompt.")

        current_role: Optional[str] = None
        current_content_parts: List[str] = []

        for msg in openai_msgs_to_convert:
            role = msg.get('role')
            content = msg.get('content', '')
            anthropic_role = "user" if role == "user" else "assistant"

            if current_role is None:
                current_role = anthropic_role
                current_content_parts = [content]
            elif anthropic_role == current_role:
                current_content_parts.append(content)
            else:
                if current_role and current_content_parts:
                    joined_content = "\n".join(filter(None, current_content_parts))
                    if joined_content:
                         anthropic_messages.append({"role": current_role, "content": joined_content})
                current_role = anthropic_role
                current_content_parts = [content]

        if current_role and current_content_parts:
             joined_content = "\n".join(filter(None, current_content_parts))
             if joined_content:
                 anthropic_messages.append({"role": current_role, "content": joined_content})

        if anthropic_messages and anthropic_messages[0]['role'] != 'user':
             log.warning("Anthropic requires the first message in 'messages' list to be 'user'. Prepending a placeholder user message.")
             anthropic_messages.insert(0, {"role": "user", "content": "(System instructions were provided separately)"})

        return anthropic_messages, system_prompt

    # Claude 4.6+ (and every 5.x, Fable, Mythos) uses adaptive thinking with an effort level;
    # Opus 4.7+ / 5.x / Fable reject budget_tokens with a 400. Older models use budget_tokens.
    _ADAPTIVE_MODEL_RE = re.compile(r"claude-(fable|mythos)\b|claude-(opus|sonnet|haiku)-(\d+)(?:-(\d{1,2}))?(?:-\d{8})?$")

    @classmethod
    def _uses_adaptive_thinking(cls, model_name: str) -> bool:
        """True for models that take thinking={type: adaptive} + output_config.effort."""
        match = cls._ADAPTIVE_MODEL_RE.match(model_name)
        if not match:
            return False  # e.g. claude-3-7-sonnet-*, claude-3-opus-*: legacy naming, legacy thinking
        if match.group(1):
            return True
        major, minor = int(match.group(3)), int(match.group(4) or 0)
        return (major, minor) >= (4, 6)

    @staticmethod
    def _get_budget_thinking_config(thinking_level: str) -> Optional[Dict[str, Any]]:
        """Maps thinking level to the legacy budget_tokens configuration (pre-4.6 models)."""
        budgets = {"low": 2048, "medium": 4096, "high": 16000}
        if thinking_level in budgets:
            return {"type": "enabled", "budget_tokens": budgets[thinking_level]}
        return None

    def _build_request(self, anthropic_messages: List[Dict[str, str]], system_prompt: Optional[str]) -> Dict[str, Any]:
        """Builds the messages.stream() kwargs. Never sets temperature/top_p/top_k (rejected by the API)."""
        model_name = self.config.model
        kwargs: Dict[str, Any] = {
            "model": model_name,
            "messages": anthropic_messages,
            "max_tokens": self.LEGACY_MAX_TOKENS,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        thinking_level = self.config.thinking_level
        if self._uses_adaptive_thinking(model_name):
            # Explicit: on Opus 4.7/4.8 omitting `thinking` means no thinking at all.
            kwargs["thinking"] = {"type": "adaptive"}
            kwargs["max_tokens"] = self.MAX_TOKENS
            if thinking_level:
                kwargs["output_config"] = {"effort": thinking_level}
        elif thinking_level:
            budget_config = self._get_budget_thinking_config(thinking_level)
            if budget_config:
                kwargs["thinking"] = budget_config
                kwargs["max_tokens"] = budget_config["budget_tokens"] + self.LEGACY_MAX_TOKENS
        log.debug(f"Anthropic thinking: {kwargs.get('thinking')}, output_config: {kwargs.get('output_config')}")
        return kwargs

    def _create(self, kwargs: Dict[str, Any]) -> Any:
        """Streams the request (large max_tokens needs streaming) and returns the final message."""
        with self.client.messages.stream(**kwargs) as stream:
            return stream.get_final_message()

    @staticmethod
    def _parse_response(api_response: Any) -> Dict[str, Any]:
        """Converts an Anthropic Message into tulp's response dict."""
        log.debug(f"Anthropic raw response: {api_response}")
        stop_reason = getattr(api_response, 'stop_reason', None) or 'unknown'
        if stop_reason == "refusal":
            details = getattr(api_response, 'stop_details', None)
            explanation = getattr(details, 'explanation', None) or getattr(details, 'category', None) or "no details"
            log.error(f"Anthropic model refused the request: {explanation}")
            return {"role": "error", "content": f"Model Refusal: {explanation}", "finish_reason": "refusal"}

        response_content = "".join(
            getattr(block, 'text', '') for block in (api_response.content or [])
            if getattr(block, 'type', None) == 'text'
        )
        finish_reason = {"end_turn": "stop", "max_tokens": "length"}.get(stop_reason, stop_reason)
        if finish_reason == "length":
            log.warning("Anthropic response truncated due to length limit (max_tokens).")
        return {
            "role": getattr(api_response, 'role', 'assistant'),
            "content": response_content,
            "finish_reason": finish_reason,
        }

    def generate(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generates a response from the Anthropic model."""
        if not ANTHROPIC_AVAILABLE:
            return {"role": "error", "content": "Anthropic library not installed.", "finish_reason": "error"}

        anthropic_messages, system_prompt = self._convert_messages(messages)
        if not anthropic_messages:
            return {"role": "error", "content": "Message list for Anthropic is empty or invalid.", "finish_reason": "error"}

        kwargs = self._build_request(anthropic_messages, system_prompt)
        assert anthropic is not None
        try:
            log.debug(f"Sending request to Anthropic model: {self.config.model}")
            return self._parse_response(self._create(kwargs))
        except anthropic.BadRequestError as e:
            # Models without thinking support (e.g. Claude 3 Opus/Haiku): retry without it.
            if "thinking" in kwargs and ("thinking" in str(e) or "budget_tokens" in str(e) or "effort" in str(e)):
                log.warning(f"Thinking parameters rejected (model might not support them): {e}. Retrying without thinking.")
                kwargs.pop("thinking", None)
                kwargs.pop("output_config", None)
                kwargs["max_tokens"] = self.LEGACY_MAX_TOKENS
                try:
                    return self._parse_response(self._create(kwargs))
                except anthropic.APIError as retry_e:
                    log.error(f"Anthropic retry without thinking failed: {retry_e}")
                    return {"role": "error", "content": f"Retry failed: {retry_e}", "finish_reason": "error"}
            log.error(f"Anthropic Bad Request: {e}")
            return {"role": "error", "content": f"Anthropic Bad Request: {e.message}", "finish_reason": "error"}
        except anthropic.APIStatusError as e:
            log.error(f"Anthropic API status error: {e.status_code} - {e.message}")
            return {"role": "error", "content": f"Anthropic API Error ({e.status_code}): {e.message}", "finish_reason": "error"}
        except anthropic.APIConnectionError as e:
            log.error(f"Anthropic API connection error: {e}")
            return {"role": "error", "content": f"Anthropic Connection Error: {e}", "finish_reason": "error"}
        except Exception as e:  # pylint: disable=broad-except
            log.error(f"Unexpected error during Anthropic generation: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return {"role": "error", "content": f"Unexpected Error: {e}", "finish_reason": "error"}
