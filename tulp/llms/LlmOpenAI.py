# tulp/llms/LlmOpenAI.py
import re
from typing import List, Dict, Any, Optional, Tuple
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
    # Warning logged during Client init or getModels/getArguments


def getModels() -> List[Dict[str, str]]:
    """Returns model definitions for OpenAI and compatible APIs."""
    if not OPENAI_AVAILABLE:
         log.warning("OpenAI library not found. OpenAI models unavailable.")
         log.warning("Install it with: pip install openai")
         return []
    # Allow gpt-*, chatgpt-*, and explicit openai.* prefixes. Use raw strings.
    return [
        {
            "idRe": r"(gpt-|chatgpt-|codex-|o[13]-|openai\.).*",
            "description": "Any OpenAI model (e.g. gpt-6-luna, gpt-6.1-sol, gpt-6-astra; https://developers.openai.com/api/docs/models) or compatible API (e.g., local Ollama with base URL). Requires API key (openai_api_key). Use 'openai.<MODEL_ID>' for unlisted models.",
        }
    ]


def getArguments() -> List[Dict[str, Any]]:
    """Returns argument definitions specific to OpenAI and compatible APIs."""
    if not OPENAI_AVAILABLE:
        return []
    return [
        {"name": "openai_api_key", "description": "OpenAI (or compatible) API Key", "default": None},
        {"name": "openai_baseurl", "description": "Override OpenAI API base URL (e.g., for local models like Ollama: http://localhost:11434/v1)", "default": None}
    ]


class Client:
    """Client for interacting with OpenAI models or compatible APIs."""
    MODEL_PREFIX = "openai."  # Explicit-provider prefix for ids the gpt-*/o* patterns don't match
    def __init__(self, config: TulpConfig):
        """Initializes the OpenAI client."""
        self.config = config
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library is not installed. Cannot use OpenAI client.")
        _import_sdk()

        api_key = config.get_llm_argument("openai_api_key")
        base_url = config.get_llm_argument("openai_baseurl")

        # API key is generally required, but provide a placeholder for local URLs if key is missing
        if not api_key:
             is_local = base_url and ('localhost' in base_url or '127.0.0.1' in base_url)
             if is_local:
                 log.warning("OpenAI API key not set, but base URL appears local. Using placeholder key 'None'. Ensure your local endpoint doesn't require authentication.")
                 api_key = "None" # Placeholder expected by some local endpoints using OpenAI format
             else:
                 log.error(f'OpenAI API key not found. Please set the {constants.ENV_VAR_PREFIX}OPENAI_API_KEY environment variable, add it to {config.config_file_path}, or use --openai_api_key.')
                 log.error("Get an API key at: https://platform.openai.com/account/api-keys")
                 raise ValueError("OpenAI API key is missing for non-local URL.")

        try:
            # Ensure OpenAI class is imported
            assert OpenAI is not None
            if base_url:
                log.info(f"Using custom OpenAI base URL: {base_url}")
                self.client = OpenAI(base_url=base_url, api_key=api_key)
            else:
                log.info("Using default OpenAI API URL.")
                self.client = OpenAI(api_key=api_key)
            # Optional: Test connection, e.g., list models (can be slow/costly)
            # log.debug("Testing OpenAI connection by listing models...")
            # self.client.models.list()
            log.info("OpenAI client initialized.")
        except Exception as e:
            log.error(f"Failed to initialize OpenAI client: {e}")
            raise ValueError(f"OpenAI client initialization failed: {e}") from e

    def list_models(self) -> List[str]:
        """Model ids served by the configured endpoint (for --list-models)."""
        return [m.id for m in self.client.with_options(timeout=constants.LIST_MODELS_TIMEOUT).models.list()]

    def _get_model_name(self) -> str:
        """Extracts the actual model name if 'openai.' prefix is used."""
        model_config_name = self.config.model
        if model_config_name.startswith("openai."):
            model_name = model_config_name[7:]
            log.debug(f"Using explicit OpenAI model name: {model_name}")
            return model_name
        # For gpt-* or chatgpt-*, use the name directly
        return model_config_name

    @staticmethod
    def _gpt_major_version(model_name: str) -> Optional[int]:
        """Returns N for gpt-N* model names (gpt-5-mini -> 5, gpt-6.1-sol -> 6), else None."""
        match = re.match(r"gpt-(\d+)", model_name.lower())
        return int(match.group(1)) if match else None

    def _is_reasoning_model(self, model_name: str) -> bool:
        """Checks if the model is an OpenAI reasoning model: o-series and GPT-5+ (gpt-5.x, gpt-6.x)."""
        normalized_model = model_name.lower()
        if re.match(r"o\d", normalized_model):
            return True
        major = self._gpt_major_version(normalized_model)
        # gpt-5-chat-* are the non-reasoning chat variants
        return major is not None and major >= 5 and "-chat" not in normalized_model

    def generate(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generates a response from the OpenAI/compatible model."""
        if not OPENAI_AVAILABLE:
             return {"role": "error", "content": "OpenAI library not installed.", "finish_reason": "error"}

        model_name = self._get_model_name()
        messages_to_send = messages # Use original messages

        use_responses = self._should_use_responses_api(model_name)
        if use_responses:
            result = self._generate_via_responses(model_name, messages_to_send)
            if result is not None:
                return result
            log.info(f"Falling back to Chat Completions endpoint for model '{model_name}'.")

        return self._generate_via_chat_completions(model_name, messages_to_send)

    def _should_use_responses_api(self, model_name: str) -> bool:
        """Determines if we should prefer the Responses API for this request."""
        if not hasattr(self.client, "responses") or not hasattr(self.client.responses, "create"):
            log.debug("OpenAI client does not expose responses.create; using chat completions.")
            return False

        base_url = self.config.get_llm_argument("openai_baseurl")
        normalized_model = model_name.lower()

        if base_url:
            # Custom base URLs are typically compatibility layers that only implement chat completions.
            if "api.openai.com" not in base_url.lower():
                return normalized_model.startswith("codex")

        # Prefer the Responses API (OpenAI's recommended endpoint) for gpt-4.1+, gpt-5+/gpt-6+ and codex.
        # o-series models (o3, o4-mini; being retired) stay on Chat Completions with reasoning_effort.
        major = self._gpt_major_version(normalized_model)
        if normalized_model.startswith(("gpt-4.1", "gpt-4.2")) or (major is not None and major >= 5):
            return True
        return "codex" in normalized_model

    def _generate_via_responses(self, model_name: str, messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Attempts to fulfill the request using the Responses API."""
        try:
            formatted_input = self._format_responses_messages(messages)
            
            params: Dict[str, Any] = {"model": model_name, "input": formatted_input}
            if self._is_reasoning_model(model_name) and self.config.thinking_level:
                params["reasoning"] = {"effort": self.config.thinking_level}
                log.debug(f"Applied reasoning effort '{self.config.thinking_level}' for {model_name}")
            try:
                api_response = self.client.responses.create(**params)
            except APIStatusError as e:
                # A model that doesn't take this effort level (or reasoning at all): retry with its default.
                if getattr(e, "status_code", None) == 400 and "reasoning" in params and "reasoning" in str(e).lower():
                    log.warning(f"Reasoning effort rejected for {model_name} ({e}); retrying with the model default.")
                    del params["reasoning"]
                    api_response = self.client.responses.create(**params)
                else:
                    raise
            log.debug(f"OpenAI responses raw object: {api_response}")
        except APIStatusError as e:
            if getattr(e, "status_code", None) in (404, 405, 501):
                log.info(f"Responses API not available at the configured endpoint (status {getattr(e, 'status_code', 'unknown')}).")
                return None
            return self._handle_openai_exception(e, model_name)
        except (AuthenticationError, NotFoundError, RateLimitError, APIConnectionError) as e:
            return self._handle_openai_exception(e, model_name)
        except Exception as e:
            log.debug("Responses API raised unexpected error; falling back to chat completions.")
            log.debug(str(e))
            import traceback
            log.debug(traceback.format_exc())
            return None

        response_content, response_role, finish_reason = self._extract_responses_output(api_response)

        if response_content is None:
            log.error("OpenAI Responses API returned no textual content.")
            return {"role": "error", "content": "OpenAI Responses API returned no content.", "finish_reason": "error"}

        return {
            "role": response_role or "assistant",
            "content": response_content,
            "finish_reason": finish_reason or "unknown"
        }

    def _generate_via_chat_completions(self, model_name: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Fallback to the legacy Chat Completions endpoint."""
        log.debug(f"Sending request to OpenAI/compatible model: {model_name}")
        
        is_reasoning = self._is_reasoning_model(model_name)

        # Prepare parameters
        params = {
            "model": model_name,
            "messages": messages,
        }
        
        # Apply reasoning_effort (thinking level) if applicable
        if is_reasoning:
            params["reasoning_effort"] = self.config.thinking_level
            # Reasoning models typically use max_completion_tokens
            params["max_completion_tokens"] = 65536 # High default for reasoning
            log.debug(f"Applied reasoning_effort='{self.config.thinking_level}' and max_completion_tokens for {model_name}")
        else:
            # Standard models
            params["temperature"] = 0.7 # Default
            # params["max_tokens"] = 4096 # Can be set if needed

        try:
            # Ensure client is valid
            assert self.client is not None
            api_response = self.client.chat.completions.create(**params)
            
            log.debug(f"OpenAI raw response object: {api_response}")

            if not api_response.choices:
                 log.error("OpenAI response contained no choices.")
                 return {"role": "error", "content": "OpenAI returned no choices.", "finish_reason": "error"}

            choice = api_response.choices[0]
            response_role = getattr(choice.message, 'role', 'assistant')
            response_content = getattr(choice.message, 'content', None)
            
            # Handle refusal (sometimes present in recent API versions)
            if hasattr(choice.message, 'refusal') and choice.message.refusal:
                log.warning(f"Model refusal: {choice.message.refusal}")
                return {"role": "error", "content": f"Model Refusal: {choice.message.refusal}", "finish_reason": "refusal"}

            if response_content is None:
                 log.warning("OpenAI response message content is None.")
                 response_content = ""

            finish_reason = getattr(choice, 'finish_reason', 'unknown')
            log.debug(f"OpenAI finish reason: {finish_reason}")

            if finish_reason == "content_filter":
                 log.error("OpenAI response stopped due to content filter.")
                 return {"role": "error", "content": "Blocked by OpenAI Content Filter", "finish_reason": "content_filter"}
            elif finish_reason == "length":
                 log.warning("OpenAI response truncated due to length limit.")

            return {
                "role": response_role,
                "content": response_content,
                "finish_reason": finish_reason
            }
        except (AuthenticationError, NotFoundError, RateLimitError, APIStatusError, APIConnectionError) as e:
            return self._handle_openai_exception(e, model_name)
        except Exception as e:
            log.error(f"Unexpected error during OpenAI generation: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return {"role": "error", "content": f"Unexpected Error: {e}", "finish_reason": "error"}

    def _format_responses_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transforms chat-completions-style messages into Responses API input format."""
        formatted_messages: List[Dict[str, Any]] = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if isinstance(content, list):
                formatted_content = [
                    self._coerce_responses_content_item(role, item) for item in content
                ]
            else:
                formatted_content = [self._coerce_responses_content_item(role, content)]

            formatted_messages.append(
                {
                    "role": role,
                    "content": formatted_content
                }
            )
        return formatted_messages

    def _coerce_responses_content_item(self, role: str, item: Any) -> Dict[str, Any]:
        """Converts chat-completions content atoms into Responses API atoms."""
        allowed_types = {
            "input_text",
            "input_image",
            "output_text",
            "refusal",
            "input_file",
            "computer_screenshot",
            "summary_text",
        }

        raw_text = item

        if isinstance(item, dict):
            item_type = item.get("type")
            if item_type in allowed_types:
                return item

            text_value = item.get("text")
            if isinstance(text_value, dict):
                text_value = text_value.get("value")
            if text_value is None:
                text_value = item.get("value")
            if text_value is not None:
                raw_text = text_value

        target_type = "output_text" if role == "assistant" else "input_text"
        coerced_text = "" if raw_text is None else str(raw_text)
        return {"type": target_type, "text": coerced_text}

    def _extract_responses_output(self, api_response: Any) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extracts text, role, and finish reason from a Responses API result."""
        response_dict: Dict[str, Any]
        if hasattr(api_response, "model_dump"):
            response_dict = api_response.model_dump()
        elif isinstance(api_response, dict):
            response_dict = api_response
        else:
            response_dict = getattr(api_response, "__dict__", {})

        text_output = getattr(api_response, "output_text", None)

        output_items = response_dict.get("output", [])
        response_role: Optional[str] = None
        collected_text_parts: List[str] = []

        if isinstance(output_items, list):
            for item in output_items:
                item_type = (item.get("type") if isinstance(item, dict) else None)
                if item_type != "message":
                    continue
                response_role = item.get("role", response_role)
                for content_item in item.get("content", []):
                    if not isinstance(content_item, dict):
                        continue
                    if content_item.get("type") != "text":
                        continue
                    text_value = content_item.get("text")
                    if isinstance(text_value, dict):
                        collected_text_parts.append(text_value.get("value", ""))
                    elif text_value is not None:
                        collected_text_parts.append(str(text_value))

        response_content = text_output or "".join(collected_text_parts) or None
        finish_reason = response_dict.get("stop_reason") or response_dict.get("status")
        return response_content, response_role, finish_reason

    def _handle_openai_exception(self, exception: Exception, model_name: str) -> Dict[str, Any]:
        """Standardizes error handling across OpenAI endpoints."""
        if isinstance(exception, AuthenticationError):
            log.error(f"OpenAI Authentication Error: {exception}. Check your API key or organization setup.")
            return {"role": "error", "content": f"OpenAI Auth Error: {exception}", "finish_reason": "error"}
        if isinstance(exception, NotFoundError):
            log.error(f"OpenAI Not Found Error: {exception}. Check model name ('{model_name}') or API endpoint/base URL.")
            return {"role": "error", "content": f"OpenAI Not Found Error: {exception}", "finish_reason": "error"}
        if isinstance(exception, RateLimitError):
            log.error(f"OpenAI API rate limit exceeded: {exception}")
            return {"role": "error", "content": "OpenAI Rate Limit Exceeded", "finish_reason": "rate_limit"}
        if isinstance(exception, APIStatusError):
            log.error(f"OpenAI API status error: {exception.status_code} - {getattr(exception, 'message', str(exception))}")
            return {
                "role": "error",
                "content": f"OpenAI API Error ({exception.status_code}): {getattr(exception, 'message', str(exception))}",
                "finish_reason": "error"
            }
        if isinstance(exception, APIConnectionError):
            log.error(f"OpenAI API connection error: {exception}")
            return {"role": "error", "content": f"OpenAI Connection Error: {exception}", "finish_reason": "error"}
        log.error(f"Unexpected error during OpenAI request: {exception}")
        import traceback
        log.debug(traceback.format_exc())
        return {"role": "error", "content": f"Unexpected Error: {exception}", "finish_reason": "error"}
