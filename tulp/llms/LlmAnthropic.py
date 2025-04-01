# tulp/llms/LlmAnthropic.py
import sys
from typing import List, Dict, Any, Tuple, Optional # Added Tuple, Optional
from ..logger import log
from ..config import TulpConfig # Use TulpConfig for type hint
from .. import constants # Import constants

# Conditional import
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None # Assign None to satisfy linters
    ANTHROPIC_AVAILABLE = False
    # Warning logged when getModels or getArguments is called, or during Client init

def getModels() -> List[Dict[str, str]]:
   """Returns model definitions for Anthropic."""
   if not ANTHROPIC_AVAILABLE:
        return []
   # Use raw string r"" for regex patterns
   return [ { "idRe": r"claude-.*", "description": "Any Anthropic Claude model (https://docs.anthropic.com/claude/docs/models-overview), requires ANTHROPIC_API_KEY"} ]

def getArguments() -> List[Dict[str, Any]]:
   """Returns argument definitions specific to Anthropic."""
   if not ANTHROPIC_AVAILABLE:
       return []
   return [{"name": "anthropic_api_key", "description": "Anthropic API key", "default": None}]


class Client:
    """Client for interacting with Anthropic's Claude models."""
    def __init__(self, config: TulpConfig):
        """Initializes the Anthropic client."""
        self.config = config
        if not ANTHROPIC_AVAILABLE:
             raise ImportError("Anthropic library is not installed. Cannot use Anthropic client.")

        api_key = config.get_llm_argument("anthropic_api_key") # Use getter method
        if not api_key:
            log.error(f'Anthropic API key not found. Please set the {constants.ENV_VAR_PREFIX}ANTHROPIC_API_KEY environment variable, add it to {config.config_file_path}, or use --anthropic_api_key.')
            log.error("If you don't have one, please create one at: https://console.anthropic.com")
            # Raise an error instead of exiting directly to allow cli.py to handle exit
            raise ValueError("Anthropic API key is missing.")
        try:
            # Ensure anthropic is imported before using it
            assert anthropic is not None
            self.client = anthropic.Anthropic(api_key=api_key)
            # Optional: Could add a quick test here, e.g., a simple ping or model list if available
            log.info("Anthropic client initialized.")
        except Exception as e:
            log.error(f"Failed to initialize Anthropic client: {e}")
            raise # Re-raise the exception

    def _convert_messages(self, messages: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        Converts OpenAI message format to Anthropic format.
        Separates the system prompt and ensures the message list starts with 'user'.
        Merges consecutive messages from the same role.

        Returns:
            A tuple containing (list_of_anthropic_messages, system_prompt_string_or_none).
        """
        if not messages:
            return [], None

        anthropic_messages = []
        system_prompt: Optional[str] = None
        openai_msgs_to_convert = messages

        # Extract system prompt if it's the first message
        if messages[0]['role'] == 'system':
            system_prompt = messages[0]['content']
            openai_msgs_to_convert = messages[1:] # Process the rest
            log.debug("Using first message as Anthropic system prompt.")

        current_role: Optional[str] = None
        current_content_parts: List[str] = []

        for msg in openai_msgs_to_convert:
            role = msg.get('role')
            content = msg.get('content', '')

            # Map roles (model is Anthropic's term for assistant)
            anthropic_role = "user" if role == "user" else "assistant"

            if current_role is None:
                # Start of messages or after completing a block
                current_role = anthropic_role
                current_content_parts = [content]
            elif anthropic_role == current_role:
                # Same role as previous, append content
                current_content_parts.append(content)
            else:
                # Role changed, finalize previous message block
                if current_role and current_content_parts:
                    # Join parts with newline, filter empty strings just in case
                    joined_content = "\n".join(filter(None, current_content_parts))
                    if joined_content: # Only add if there's content
                         anthropic_messages.append({"role": current_role, "content": joined_content})
                # Start new block
                current_role = anthropic_role
                current_content_parts = [content]

        # Append the last message block
        if current_role and current_content_parts:
             joined_content = "\n".join(filter(None, current_content_parts))
             if joined_content:
                 anthropic_messages.append({"role": current_role, "content": joined_content})

        # Anthropic specific validation: first message in the list must be 'user'.
        if anthropic_messages and anthropic_messages[0]['role'] != 'user':
             log.warning("Anthropic requires the first message in 'messages' list to be 'user'. Prepending a placeholder user message.")
             # This often indicates a prompt structure issue.
             anthropic_messages.insert(0, {"role": "user", "content": "(System instructions were provided separately)"}) # Placeholder

        log.debug(f"Converted messages for Anthropic (excluding system): {len(anthropic_messages)} messages")
        return anthropic_messages, system_prompt


    def generate(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generates a response from the Anthropic model."""
        if not ANTHROPIC_AVAILABLE:
             return {"role": "error", "content": "Anthropic library not installed.", "finish_reason": "error"}

        anthropic_messages, system_prompt = self._convert_messages(messages)

        if not anthropic_messages:
             # This might happen if only a system prompt was provided initially
             log.error("Cannot send empty message list to Anthropic (only system prompt provided?).")
             # Anthropic needs at least one user message.
             # Fail clearly for now.
             return {"role": "error", "content": "Message list for Anthropic is empty or invalid.", "finish_reason": "error"}

        try:
            log.debug(f"Sending request to Anthropic model: {self.config.model}")
            # Ensure anthropic is imported before using it
            assert anthropic is not None
            api_response = self.client.messages.create(
                model=self.config.model,
                messages=anthropic_messages,
                system=system_prompt, # Pass system prompt here
                max_tokens=4096 # Consider making this configurable via TULP_MAX_TOKENS_OUT or similar
            )
            log.debug(f"Anthropic raw response: {api_response}")

            # Extract necessary information safely
            response_role = getattr(api_response, 'role', 'assistant') # Default to assistant
            response_content = ""
            if api_response.content and isinstance(api_response.content, list):
                 # Find the first text block
                 for block in api_response.content:
                      if getattr(block, 'type', None) == 'text':
                           response_content = getattr(block, 'text', '')
                           break # Take the first text block found

            finish_reason = getattr(api_response, 'stop_reason', 'unknown')

            # Map Anthropic stop reasons to OpenAI-like reasons if needed, or keep Anthropic's
            # Anthropic reasons: "end_turn", "max_tokens", "stop_sequence", "tool_use" (tool_use not handled here)
            # OpenAI reasons: "stop", "length", "tool_calls", "content_filter", "function_call"
            mapped_reason = finish_reason
            if finish_reason == "end_turn":
                 mapped_reason = "stop"
            elif finish_reason == "max_tokens":
                 mapped_reason = "length"
            # No direct mapping for content_filter from stop_reason, might need error handling based on response content or status?

            log.debug(f"Anthropic mapped finish reason: {mapped_reason}")

            return {
                "role": response_role,
                "content": response_content,
                "finish_reason": mapped_reason # Return the mapped reason
            }
        # Use specific exceptions from the library if available
        except anthropic.APIStatusError as e:
            log.error(f"Anthropic API status error: {e.status_code} - {e.message}")
            content = f"Anthropic API Error ({e.status_code}): {getattr(e, 'message', str(e))}"
            # Add more specific checks if needed
            if e.status_code == 401:
                content = f"Anthropic Authentication Error ({e.status_code}). Check your API key."
            elif e.status_code == 404:
                 content = f"Anthropic API endpoint/model not found ({e.status_code}). Check model name."
            return {"role": "error", "content": content, "finish_reason": "error"}
        except anthropic.APITimeoutError as e:
            log.error(f"Anthropic API timeout error: {e}")
            return {"role": "error", "content": "Anthropic API request timed out.", "finish_reason": "timeout"}
        except anthropic.APIConnectionError as e:
            log.error(f"Anthropic API connection error: {e}")
            return {"role": "error", "content": "Anthropic Connection Error", "finish_reason": "error"}
        except Exception as e:
            log.error(f"Unexpected error during Anthropic generation: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return {"role": "error", "content": f"Unexpected Error: {e}", "finish_reason": "error"}

# Ensure constants is imported if used within the module
# from .. import constants # Already imported at the top
