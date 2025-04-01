# tulp/llms/LlmGroq.py
import sys
from typing import List, Dict, Any
from ..logger import log
from ..config import TulpConfig
from .. import constants

# Conditional import for groq
try:
    from groq import Groq, APIConnectionError, APIStatusError, RateLimitError
    GROQ_AVAILABLE = True
except ImportError:
    Groq = None
    APIConnectionError = None
    APIStatusError = None
    RateLimitError = None
    GROQ_AVAILABLE = False
    # Warning logged during Client init or getModels/getArguments

def getModels() -> List[Dict[str, str]]:
   """Returns model definitions for Groq."""
   if not GROQ_AVAILABLE:
        log.warning("Groq library not found. Groq models unavailable.")
        log.warning("Install it with: pip install groq")
        return []
   # Use raw string for regex
   return [ { "idRe": r"groq\..*", "description": "Any Groq model id using the prefix 'groq.', requires GROQ_API_KEY. Check available models at https://console.groq.com/docs/models" }]

def getArguments() -> List[Dict[str, Any]]:
   """Returns argument definitions specific to Groq."""
   if not GROQ_AVAILABLE:
        return []
   return [{"name": "groq_api_key", "description": "Groq Cloud API Key", "default": None}]


class Client:
    """Client for interacting with Groq's language models."""
    def __init__(self, config: TulpConfig):
        """Initializes the Groq client."""
        self.config = config
        if not GROQ_AVAILABLE:
            raise ImportError("Groq library is not installed. Cannot use Groq client.")

        api_key = config.get_llm_argument("groq_api_key")
        if not api_key:
            log.error(f'Groq API key not found. Please set the {constants.ENV_VAR_PREFIX}GROQ_API_KEY environment variable, add it to {config.config_file_path}, or use --groq_api_key.')
            log.error("If you don't have one, sign up at: https://console.groq.com/")
            raise ValueError("Groq API key is missing.")

        try:
            # Ensure Groq is imported
            assert Groq is not None
            self.client = Groq(api_key=api_key)
            # Optional: Test connection, e.g., list models
            # self.client.models.list() # Makes an API call, potentially slow/costly
            log.info("Groq client initialized.")
        except Exception as e:
            log.error(f"Failed to initialize Groq client: {e}")
            # Add specific error checks if Groq client raises unique exceptions on init
            raise ValueError(f"Groq client initialization failed: {e}") from e

    def _get_model_name(self) -> str:
        """Extracts the actual model name from the configured name (strips 'groq.')."""
        model_config_name = self.config.model
        if model_config_name.startswith("groq."):
            model_name = model_config_name[5:]
            log.debug(f"Using Groq model: {model_name}")
            return model_name
        # If the model name doesn't start with groq. but was matched by the regex,
        # it's likely an error or unexpected state. Log a warning.
        log.warning(f"Model name '{model_config_name}' matched Groq provider but doesn't start with 'groq.'. Using it as is, but this might fail.")
        return model_config_name

    # Groq uses OpenAI's message format, so no conversion needed generally
    # If specific adaptations become necessary, add a _convert_messages method here.

    def generate(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generates a response from the Groq model."""
        if not GROQ_AVAILABLE:
             return {"role": "error", "content": "Groq library not installed.", "finish_reason": "error"}

        model_name = self._get_model_name()
        log.debug(f"Sending request to Groq model: {model_name}")

        # Log request details (optional, can be verbose)
        # for i, req in enumerate(messages):
        #     log.debug(f"Groq REQ {i}: Role={req.get('role')} Content='{req.get('content', '')[:100]}...'")

        try:
            # Ensure Groq client is available
            assert self.client is not None
            # Groq's API mirrors OpenAI's chat completions
            api_response = self.client.chat.completions.create(
                messages=messages,
                model=model_name,
                # Optional parameters (adjust as needed, keep defaults minimal for now)
                temperature=0.7, # A common default, adjust if needed
                max_tokens=4096, # Groq models often have large contexts, set a reasonable limit
                # top_p=1,
                # stop=None,
                # stream=False, # Streaming not implemented in this core loop
            )
            log.debug(f"Groq raw response object: {api_response}")

            if not api_response.choices:
                 log.error("Groq response contained no choices.")
                 # Check if usage or other fields indicate an error
                 usage = getattr(api_response, 'usage', None)
                 log.debug(f"Groq Usage (if available): {usage}")
                 return {"role": "error", "content": "Groq returned no choices.", "finish_reason": "error"}

            # Extract info from the first choice
            choice = api_response.choices[0]
            response_role = getattr(choice.message, 'role', 'assistant')
            # Handle potential None content
            response_content = getattr(choice.message, 'content', None)
            if response_content is None:
                 log.warning("Groq response message content is None.")
                 response_content = "" # Default to empty string

            finish_reason = getattr(choice, 'finish_reason', 'unknown')

            log.debug(f"Groq finish reason: {finish_reason}")

            # Handle potential content filtering or other issues signaled by finish_reason
            if finish_reason == "content_filter":
                 log.error("Groq response stopped due to content filter.")
                 return {"role": "error", "content": "Blocked by Groq Content Filter", "finish_reason": "content_filter"}
            elif finish_reason == "length":
                 log.warning("Groq response truncated due to length limit (max_tokens).")

            return {
                "role": response_role,
                "content": response_content,
                "finish_reason": finish_reason # Return Groq's reason directly
            }
        # Catch specific Groq/OpenAI-like errors
        except APIStatusError as e:
            log.error(f"Groq API status error: {e.status_code} - {getattr(e, 'message', str(e))}")
            content = f"Groq API Error ({e.status_code}): {getattr(e, 'message', str(e))}"
            if e.status_code == 401: content = f"Groq Authentication Error ({e.status_code}). Check API key."
            elif e.status_code == 404: content = f"Groq Model '{model_name}' not found ({e.status_code})."
            elif e.status_code == 429: content = f"Groq Rate Limit Exceeded ({e.status_code})."
            return {"role": "error", "content": content, "finish_reason": "error"}
        except RateLimitError as e: # Catch separately if needed
            log.error(f"Groq API rate limit exceeded: {e}")
            return {"role": "error", "content": "Groq Rate Limit Exceeded", "finish_reason": "rate_limit"}
        except APIConnectionError as e:
            log.error(f"Groq API connection error: {e}")
            return {"role": "error", "content": f"Groq Connection Error: {e}", "finish_reason": "error"}
        except Exception as e:
            log.error(f"Unexpected error during Groq generation: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return {"role": "error", "content": f"Unexpected Error: {e}", "finish_reason": "error"}

# Ensure constants is imported if used within the module
# from .. import constants # Already imported
