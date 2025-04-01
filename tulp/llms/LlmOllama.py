# tulp/llms/LlmOllama.py
import sys
from typing import List, Dict, Any
from ..logger import log
from ..config import TulpConfig
from .. import constants

# Conditional import for ollama
try:
    from ollama import Client as OllamaApiClient, ResponseError, RequestError # Import specific errors
    OLLAMA_AVAILABLE = True
except ImportError:
    OllamaApiClient = None
    ResponseError = None
    RequestError = None
    OLLAMA_AVAILABLE = False
    # Warning logged during Client init or getModels/getArguments


def getModels() -> List[Dict[str, str]]:
   """Returns model definitions for Ollama."""
   if not OLLAMA_AVAILABLE:
        log.warning("Ollama library not found. Ollama models unavailable.")
        log.warning("Install it with: pip install ollama")
        return []
   # Use raw string for regex
   return [ { "idRe": r"ollama\..*", "description": "Any Ollama model prefixed with 'ollama.', requires Ollama service running (check --ollama_host)."}]

def getArguments() -> List[Dict[str, Any]]:
   """Returns argument definitions specific to Ollama."""
   if not OLLAMA_AVAILABLE:
       return []
   # Provide the default value directly from constants or a sensible default
   default_host = "http://127.0.0.1:11434"
   return [{"name": "ollama_host", "description": f"Ollama host URL (default: {default_host})", "default": default_host}]


class Client:
    """Client for interacting with local Ollama models."""
    def __init__(self, config: TulpConfig):
        """Initializes the Ollama client."""
        self.config = config
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama library is not installed. Cannot use Ollama client.")

        ollama_host = config.get_llm_argument("ollama_host") # Already has default handling via config
        if not ollama_host:
             # Should not happen if default is set correctly, but safeguard
             ollama_host = "http://127.0.0.1:11434"
             log.warning(f"Ollama host fallback to default: {ollama_host}")

        try:
            # Ensure library is loaded
            assert OllamaApiClient is not None
            self.client = OllamaApiClient(host=ollama_host)
            # Test connection by listing local models. This confirms the host is reachable.
            log.debug(f"Testing connection to Ollama host: {ollama_host}")
            self.client.list() # This will raise RequestError if connection fails
            log.info(f"Ollama client initialized and connected to: {ollama_host}")
        except RequestError as e:
             log.error(f"Failed to connect to Ollama host '{ollama_host}'. Is the Ollama service running and accessible? Error: {e}")
             # Raise a standard ConnectionError for cli.py to catch
             raise ConnectionError(f"Could not connect to Ollama at {ollama_host}") from e
        except Exception as e:
            log.error(f"Failed to initialize Ollama client: {e}")
            raise ValueError(f"Ollama client initialization failed: {e}") from e

    def _get_model_name(self) -> str:
        """Extracts the actual model name from the configured name (strips 'ollama.')."""
        model_config_name = self.config.model
        if model_config_name.startswith("ollama."):
            model_name = model_config_name[7:]
            log.debug(f"Using Ollama model: {model_name}")
            return model_name
        # If name doesn't start with ollama. but matched regex, log warning
        log.warning(f"Model name '{model_config_name}' matched Ollama provider but doesn't start with 'ollama.'. Using it as is.")
        return model_config_name

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Converts OpenAI message format to Ollama format if needed.
        Currently merges consecutive messages of the same role for robustness.
        """
        ollama_messages = []
        current_role: str | None = None
        current_content_parts: List[str] = []

        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')

            # Map roles (system, user, assistant are generally supported)
            if role not in ['system', 'user', 'assistant']:
                 log.warning(f"Treating unexpected role '{role}' as 'user' for Ollama.")
                 ollama_role = 'user'
            else:
                 ollama_role = role

            if current_role is None:
                current_role = ollama_role
                current_content_parts = [content]
            elif ollama_role == current_role:
                # Merge content for the same role
                current_content_parts.append(content)
            else:
                # Role changed, finalize previous block
                if current_role and current_content_parts:
                    joined_content = "\n".join(filter(None, current_content_parts))
                    if joined_content: # Avoid empty messages unless maybe assistant?
                        ollama_messages.append({"role": current_role, "content": joined_content})
                current_role = ollama_role
                current_content_parts = [content]

        # Append the last block
        if current_role and current_content_parts:
            joined_content = "\n".join(filter(None, current_content_parts))
            if joined_content:
                ollama_messages.append({"role": current_role, "content": joined_content})

        log.debug(f"Messages prepared for Ollama: {len(ollama_messages)} messages")
        return ollama_messages


    def generate(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generates a response from the Ollama model."""
        if not OLLAMA_AVAILABLE:
             return {"role": "error", "content": "Ollama library not installed.", "finish_reason": "error"}

        model_name = self._get_model_name()
        ollama_messages = self._convert_messages(messages)

        if not ollama_messages:
             log.error("Cannot send empty message list to Ollama.")
             return {"role": "error", "content": "Empty message list.", "finish_reason": "error"}

        log.debug(f"Sending request to Ollama model: {model_name}")
        try:
             # Ensure client is valid
             assert self.client is not None
             response = self.client.chat(
                model=model_name,
                messages=ollama_messages,
                # Add options if needed, e.g., from config
                # options={'temperature': config.get_llm_argument('temperature', 0.8)}
             )
             log.debug(f"Ollama raw response: {response}")

             # --- Extract information Robustly ---
             if not isinstance(response, dict):
                  log.error(f"Ollama response is not a dictionary: {type(response)}")
                  return {"role": "error", "content": "Invalid Ollama response type", "finish_reason": "error"}

             message_data = response.get('message')
             if not isinstance(message_data, dict):
                  log.error(f"Ollama response missing or invalid 'message' dictionary: {message_data}")
                  err_msg = response.get('error', 'Unknown error structure in response.')
                  return {"role": "error", "content": f"Ollama Error: {err_msg}", "finish_reason": "error"}

             response_role = message_data.get('role', 'assistant') # Default to assistant
             response_content = message_data.get('content', '')
             # Determine finish reason - 'done' boolean indicates completion normally.
             # Lack of 'done' or False might mean streaming or error, but library handles non-streaming.
             is_done = response.get('done', False)
             # Map to OpenAI-like reasons if possible. Assume 'stop' if done.
             # Need to investigate how Ollama signals other reasons like length limits.
             finish_reason = "stop" if is_done else "unknown"

             # Log optional performance stats if available
             eval_count = response.get('eval_count')
             eval_duration = response.get('eval_duration')
             if eval_count is not None:
                 log.debug(f"Ollama eval_count: {eval_count}, eval_duration: {eval_duration}ns")

             return {
                "role": response_role,
                "content": response_content,
                "finish_reason": finish_reason
             }
        # Catch specific Ollama errors
        except ResponseError as e:
             # Handle errors like model not found, permissions etc.
             err_msg = getattr(e, 'error', str(e))
             log.error(f"Ollama API response error: {e.status_code} - {err_msg}")
             content = f"Ollama Error ({e.status_code}): {err_msg}"
             if e.status_code == 404 or ("model" in err_msg.lower() and "not found" in err_msg.lower()):
                 content = f"Ollama model '{model_name}' not found locally. Pull it first: `ollama pull {model_name}`"
             return {"role": "error", "content": content, "finish_reason": "error"}
        except RequestError as e:
            # Handle connection errors more specifically if possible
            log.error(f"Ollama connection/request error: {e}")
            return {"role": "error", "content": f"Ollama Connection/Request Error: {e}", "finish_reason": "error"}
        except Exception as e:
            log.error(f"Unexpected error during Ollama generation: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return {"role": "error", "content": f"Unexpected Error: {e}", "finish_reason": "error"}

# Ensure constants is imported if used within the module
# from .. import constants # Already imported
