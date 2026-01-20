# tulp/llms/LlmAnthropic.py
import sys
from typing import List, Dict, Any, Tuple, Optional
from ..logger import log
from ..config import TulpConfig
from .. import constants

# Conditional import
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
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

    def _get_thinking_config(self, thinking_level: str) -> Optional[Dict[str, Any]]:
        """
        Maps thinking level to Anthropic thinking configuration (budget_tokens).
        Returns None if mapping isn't appropriate or for models that don't support it (handled by caller).
        
        Note: Currently assumes using the 'thinking' parameter which is standard for Sonnet 3.5/3.7 thinking modes.
        'effort' parameter is cleaner but currently beta/opus-only.
        """
        # Heuristic mapping for budget tokens
        # Must be careful: max_tokens must be > budget_tokens
        if thinking_level == "low":
            return {"type": "enabled", "budget_tokens": 2048}
        elif thinking_level == "medium":
            return {"type": "enabled", "budget_tokens": 4096}
        elif thinking_level == "high":
            return {"type": "enabled", "budget_tokens": 16000} # Requires very high max_tokens
        return None

    def generate(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generates a response from the Anthropic model."""
        if not ANTHROPIC_AVAILABLE:
             return {"role": "error", "content": "Anthropic library not installed.", "finish_reason": "error"}

        anthropic_messages, system_prompt = self._convert_messages(messages)

        if not anthropic_messages:
             return {"role": "error", "content": "Message list for Anthropic is empty or invalid.", "finish_reason": "error"}

        # Determine thinking config
        thinking_config = None
        max_tokens = 4096 # Default
        
        # Check if thinking is requested via level (default is low, so always check unless 'none'?)
        # User might not want thinking for all models. We should only enable if model supports it?
        # For now, we only apply if the user explicitly set it via arg or config, 
        # but defaulting to 'low' means it might apply broadly.
        # We need a safeguard. Let's apply it if the model name suggests capability or we assume modern Claude.
        # However, applying thinking to models that don't support it might error.
        # Safe strategy: Only apply if model name contains specific keywords or just try/catch?
        # Anthropic docs say thinking is a specific parameter.
        
        # NOTE: For now, I will NOT enable thinking by default unless model is known to support it 
        # or if I can detect it. Since 'claude-3-7' or similar is likely target.
        # But if the user passed --thinking-level, they expect it.
        # Let's map the level. 
        
        # To avoid breaking older models, we might check if 'sonnet' or 'opus' is in name
        # OR simply trust the API to ignore or error (and we handle error).
        # Actually, let's just set the token budget based on level.
        
        # Adjust max_tokens to accommodate thinking
        if self.config.thinking_level:
             thinking_config = self._get_thinking_config(self.config.thinking_level)
             if thinking_config:
                 # Ensure max_tokens is higher than budget
                 budget = thinking_config["budget_tokens"]
                 # Set max_tokens to budget + reasonable output buffer (e.g. 4096)
                 max_tokens = max(max_tokens, budget + 4096)
                 # Cap at some reasonable limit for API (e.g. 64k or 128k supported by Anthropic)
                 max_tokens = min(max_tokens, 64000) 
                 log.debug(f"Enabled Anthropic thinking: {thinking_config}, adjusted max_tokens: {max_tokens}")

        try:
            log.debug(f"Sending request to Anthropic model: {self.config.model}")
            assert anthropic is not None
            
            # Prepare kwargs
            kwargs = {
                "model": self.config.model,
                "messages": anthropic_messages,
                "system": system_prompt,
                "max_tokens": max_tokens
            }
            
            # Add thinking if configured
            if thinking_config:
                kwargs["thinking"] = thinking_config

            api_response = self.client.messages.create(**kwargs)
            log.debug(f"Anthropic raw response: {api_response}")

            response_role = getattr(api_response, 'role', 'assistant')
            response_content = ""
            if api_response.content and isinstance(api_response.content, list):
                 for block in api_response.content:
                      if getattr(block, 'type', None) == 'text':
                           response_content = getattr(block, 'text', '')
                           break 

            finish_reason = getattr(api_response, 'stop_reason', 'unknown')
            mapped_reason = finish_reason
            if finish_reason == "end_turn":
                 mapped_reason = "stop"
            elif finish_reason == "max_tokens":
                 mapped_reason = "length"

            return {
                "role": response_role,
                "content": response_content,
                "finish_reason": mapped_reason
            }
        except anthropic.BadRequestError as e:
            # Handle case where thinking might not be supported by the specific model
            if "thinking" in str(e) or "budget_tokens" in str(e):
                log.warning(f"Thinking parameter failed (model might not support it): {e}. Retrying without thinking.")
                if "thinking" in kwargs:
                    del kwargs["thinking"]
                    try:
                        api_response = self.client.messages.create(**kwargs)
                        # Process response as above... (simplified duplication for now)
                        response_role = getattr(api_response, 'role', 'assistant')
                        response_content = ""
                        for block in api_response.content:
                            if getattr(block, 'type', None) == 'text':
                                response_content = getattr(block, 'text', '')
                                break
                        return {"role": response_role, "content": response_content, "finish_reason": "stop"}
                    except Exception as retry_e:
                        return {"role": "error", "content": f"Retry failed: {retry_e}", "finish_reason": "error"}
            
            log.error(f"Anthropic Bad Request: {e}")
            return {"role": "error", "content": f"Anthropic Bad Request: {e.message}", "finish_reason": "error"}

        except anthropic.APIStatusError as e:
            log.error(f"Anthropic API status error: {e.status_code} - {e.message}")
            return {"role": "error", "content": f"Anthropic API Error ({e.status_code}): {e.message}", "finish_reason": "error"}
        except Exception as e:
            log.error(f"Unexpected error during Anthropic generation: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return {"role": "error", "content": f"Unexpected Error: {e}", "finish_reason": "error"}
