# tulp/llms/LlmOpenAI.py
import sys
from typing import List, Dict, Any
from ..logger import log
from ..config import TulpConfig
from .. import constants

# Conditional import for openai
try:
    from openai import OpenAI, APIConnectionError, APIStatusError, RateLimitError, AuthenticationError, NotFoundError
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    APIConnectionError = None
    APIStatusError = None
    RateLimitError = None
    AuthenticationError = None
    NotFoundError = None
    OPENAI_AVAILABLE = False
    # Warning logged during Client init or getModels/getArguments


def getModels() -> List[Dict[str, str]]:
    """Returns model definitions for OpenAI and compatible APIs."""
    if not OPENAI_AVAILABLE:
         log.warning("OpenAI library not found. OpenAI models unavailable.")
         log.warning("Install it with: pip install openai")
         return []
    # Allow gpt-*, chatgpt-*, and explicit openai.* prefixes. Use raw strings.
    return [ { "idRe": r"(gpt-|chatgpt-|openai\.).*", "description": "Any OpenAI model (https://platform.openai.com/docs/models) or compatible API (e.g., local Ollama with base URL). Requires API key (openai_api_key). Use 'openai.<MODEL_ID>' for unlisted models." } ]


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
    def __init__(self, config: TulpConfig):
        """Initializes the OpenAI client."""
        self.config = config
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library is not installed. Cannot use OpenAI client.")

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

    def _get_model_name(self) -> str:
        """Extracts the actual model name if 'openai.' prefix is used."""
        model_config_name = self.config.model
        if model_config_name.startswith("openai."):
            model_name = model_config_name[7:]
            log.debug(f"Using explicit OpenAI model name: {model_name}")
            return model_name
        # For gpt-* or chatgpt-*, use the name directly
        return model_config_name

    # No message conversion needed as Groq and Ollama (via openai_baseurl) use OpenAI format.

    def generate(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generates a response from the OpenAI/compatible model."""
        if not OPENAI_AVAILABLE:
             return {"role": "error", "content": "OpenAI library not installed.", "finish_reason": "error"}

        model_name = self._get_model_name()
        messages_to_send = messages # Use original messages

        log.debug(f"Sending request to OpenAI/compatible model: {model_name}")
        # Log request details (optional)
        # for i, req in enumerate(messages_to_send):
        #      log.debug(f"OpenAI REQ {i}: Role={req.get('role')} Content='{req.get('content', '')[:100]}...'")

        try:
            # Ensure client is valid
            assert self.client is not None
            api_response = self.client.chat.completions.create(
                model=model_name,
                messages=messages_to_send
                # Add other parameters like temperature, max_tokens if needed from config
                # temperature=config.get_llm_argument('temperature', 0.7), # Example
                # max_tokens=config.get_llm_argument('max_tokens_out', 4096) # Example
            )
            log.debug(f"OpenAI raw response object: {api_response}")

            if not api_response.choices:
                 log.error("OpenAI response contained no choices.")
                 # Check usage or system_fingerprint for clues if needed
                 return {"role": "error", "content": "OpenAI returned no choices.", "finish_reason": "error"}

            choice = api_response.choices[0]
            # Safely access attributes, providing defaults
            response_role = getattr(choice.message, 'role', 'assistant')
            response_content = getattr(choice.message, 'content', None)
            if response_content is None:
                 log.warning("OpenAI response message content is None.")
                 response_content = "" # Default to empty string

            finish_reason = getattr(choice, 'finish_reason', 'unknown')

            log.debug(f"OpenAI finish reason: {finish_reason}")

            # Handle specific finish reasons
            if finish_reason == "content_filter":
                 log.error("OpenAI response stopped due to content filter.")
                 return {"role": "error", "content": "Blocked by OpenAI Content Filter", "finish_reason": "content_filter"}
            elif finish_reason == "length":
                 log.warning("OpenAI response truncated due to length limit (max_tokens or context window).")
                 # Return truncated content, core logic should be aware via finish_reason

            return {
                "role": response_role,
                "content": response_content,
                "finish_reason": finish_reason # Return OpenAI's reason directly
            }
        # Catch specific OpenAI errors
        except AuthenticationError as e:
            log.error(f"OpenAI Authentication Error: {e}. Check your API key or organization setup.")
            return {"role": "error", "content": f"OpenAI Auth Error: {e}", "finish_reason": "error"}
        except NotFoundError as e:
             log.error(f"OpenAI Not Found Error: {e}. Check model name ('{model_name}') or API endpoint/base URL.")
             return {"role": "error", "content": f"OpenAI Not Found Error: {e}", "finish_reason": "error"}
        except RateLimitError as e:
            log.error(f"OpenAI API rate limit exceeded: {e}")
            return {"role": "error", "content": "OpenAI Rate Limit Exceeded", "finish_reason": "rate_limit"}
        except APIStatusError as e:
            # Handle other status errors (e.g., 5xx server errors)
            log.error(f"OpenAI API status error: {e.status_code} - {getattr(e, 'message', str(e))}")
            return {"role": "error", "content": f"OpenAI API Error ({e.status_code}): {getattr(e, 'message', str(e))}", "finish_reason": "error"}
        except APIConnectionError as e:
            log.error(f"OpenAI API connection error: {e}")
            return {"role": "error", "content": f"OpenAI Connection Error: {e}", "finish_reason": "error"}
        except Exception as e:
            # Catch unexpected errors
            log.error(f"Unexpected error during OpenAI generation: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return {"role": "error", "content": f"Unexpected Error: {e}", "finish_reason": "error"}

# Ensure constants is imported if used within the module
# from .. import constants # Already imported
