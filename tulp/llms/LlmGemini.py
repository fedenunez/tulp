# tulp/llms/LlmGemini.py
import sys
from typing import List, Dict, Any, Optional
from ..logger import log
from ..config import TulpConfig
from .. import constants

# Conditional import for google-genai (new SDK)
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GEMINI_AVAILABLE = False
    # Warning logged during Client init or getModels/getArguments

DEFAULT_TEMPERATURE = 1.0
MAX_TEMPERATURE = 2.0
TEMPERATURE_INCREMENT = 0.33
REQUEST_TIMEOUT = 900


def getModels() -> List[Dict[str, str]]:
    """Returns model definitions for Google Gemini."""
    if not GEMINI_AVAILABLE:
        log.warning("Google GenAI library (google-genai) not found. Gemini models unavailable. Install with: pip install google-genai")
        return []
    return [{
        "idRe": r"gemini.*",
        "description": "Any Google Gemini model (https://ai.google.dev/gemini-api/docs/models/gemini), requires GEMINI_API_KEY"
    }]


def getArguments() -> List[Dict[str, Any]]:
    """Returns argument definitions specific to Gemini."""
    if not GEMINI_AVAILABLE:
        return []
    return [{"name": "gemini_api_key", "description": "Google AI (Gemini) API Key", "default": None}]


class Client:
    """Client for interacting with Google's Gemini models via google-genai SDK."""

    def __init__(self, config: TulpConfig):
        """Initializes the Gemini client."""
        self.config = config
        if not GEMINI_AVAILABLE:
            raise ImportError("Google GenAI library (google-genai) is not installed. Install with: pip install google-genai")

        api_key = config.get_llm_argument("gemini_api_key")
        if not api_key:
            log.error(
                f'Gemini API key not found. Please set the {constants.ENV_VAR_PREFIX}GEMINI_API_KEY '
                f'environment variable, add it to {config.config_file_path}, or use --gemini_api_key.'
            )
            raise ValueError("Gemini API key is missing.")

        try:
            self.client = genai.Client(api_key=api_key)
            log.info("Gemini client initialized (google-genai SDK).")
        except Exception as e:
            log.error(f"Failed to initialize Gemini client: {e}")
            raise ValueError(f"Gemini client initialization failed: {e}") from e

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[types.Content]:
        """Converts OpenAI message format to Gemini's Content format."""
        gemini_contents = []
        current_role: Optional[str] = None
        current_parts: List[str] = []

        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')

            # Map roles: Gemini uses 'user' and 'model'
            if role == 'assistant' or role == 'model':
                gemini_role = 'model'
            elif role == 'user':
                gemini_role = 'user'
            else:
                gemini_role = 'user'

            if current_role is None:
                current_role = gemini_role
                current_parts = [content]
            elif gemini_role == current_role:
                current_parts.append(content)
            else:
                if current_role and current_parts:
                    joined_content = "\n".join(filter(None, current_parts))
                    if joined_content:
                        gemini_contents.append(types.Content(
                            role=current_role,
                            parts=[types.Part.from_text(text=joined_content)]
                        ))
                current_role = gemini_role
                current_parts = [content]

        if current_role and current_parts:
            joined_content = "\n".join(filter(None, current_parts))
            if joined_content:
                gemini_contents.append(types.Content(
                    role=current_role,
                    parts=[types.Part.from_text(text=joined_content)]
                ))

        # Gemini validation: Cannot end with 'model' role
        if gemini_contents and gemini_contents[-1].role == 'model':
            log.warning("Gemini doesn't allow conversation history to end with 'model' role. Appending placeholder.")
            gemini_contents.append(types.Content(
                role='user',
                parts=[types.Part.from_text("(Continue)")]
            ))

        return gemini_contents

    def _is_thinking_model(self) -> bool:
        """Check if the model supports thinking (Gemini 2.5+ or 3.x)."""
        model_lower = self.config.model.lower()
        return "2.5" in model_lower or "gemini-3" in model_lower

    def _get_thinking_level(self) -> Optional[str]:
        """Maps config thinking level to Gemini thinking level string."""
        if not self._is_thinking_model():
            log.debug(f"Model {self.config.model} does not support thinking")
            return None

        # Gemini 3 uses thinking_level: 'minimal', 'low', 'medium', 'high'
        # Gemini 2.5 uses thinking_budget (tokens)
        # We'll use thinking_level for simplicity as it's the newer approach
        level = self.config.thinking_level
        if level in ('low', 'medium', 'high'):
            return level
        return 'low'  # Default

    def _get_generation_config(self, system_instruction: Optional[str] = None) -> types.GenerateContentConfig:
        """Constructs GenerateContentConfig with optional thinking parameters."""
        config_args = {
            "temperature": DEFAULT_TEMPERATURE,
        }

        if system_instruction:
            config_args["system_instruction"] = system_instruction

        # Add thinking config for supported models
        thinking_level = self._get_thinking_level()
        if thinking_level:
            try:
                config_args["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_level)
                log.debug(f"Enabled thinking with level '{thinking_level}' for model {self.config.model}")
            except Exception as e:
                log.warning(f"Could not configure thinking: {e}")

        return types.GenerateContentConfig(**config_args)

    def generate(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generates a response from the Gemini model."""
        if not GEMINI_AVAILABLE:
            return {"role": "error", "content": "Google GenAI library not installed.", "finish_reason": "error"}

        # Extract system instruction if present
        system_instruction: Optional[str] = None
        openai_msgs_to_process = messages
        if messages and messages[0]['role'] == 'system':
            system_instruction = messages[0]['content']
            openai_msgs_to_process = messages[1:]

        gemini_contents = self._convert_messages(openai_msgs_to_process)

        if not gemini_contents:
            return {"role": "error", "content": "Empty message history.", "finish_reason": "error"}

        generation_config = self._get_generation_config(system_instruction)
        current_temperature = DEFAULT_TEMPERATURE
        retry_without_thinking = False

        while True:
            log.debug(f"Sending request to Gemini model {self.config.model}...")
            try:
                # Build config, potentially without thinking on retry
                if retry_without_thinking:
                    config_args = {"temperature": current_temperature}
                    if system_instruction:
                        config_args["system_instruction"] = system_instruction
                    generation_config = types.GenerateContentConfig(**config_args)

                response = self.client.models.generate_content(
                    model=self.config.model,
                    contents=gemini_contents,
                    config=generation_config
                )

                # Check for blocked prompt
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    feedback = response.prompt_feedback
                    if hasattr(feedback, 'block_reason') and feedback.block_reason:
                        block_reason = str(feedback.block_reason)
                        return {"role": "error", "content": f"Blocked by Gemini (Prompt): {block_reason}", "finish_reason": "SAFETY"}

                # Check candidates
                if not response.candidates:
                    return {"role": "error", "content": "Gemini returned no candidates", "finish_reason": "error"}

                candidate = response.candidates[0]
                finish_reason = str(candidate.finish_reason) if hasattr(candidate, 'finish_reason') else "unknown"

                if "SAFETY" in finish_reason.upper():
                    return {"role": "error", "content": "Blocked by Gemini Safety Filter", "finish_reason": "SAFETY"}

                if "RECITATION" in finish_reason.upper():
                    if current_temperature >= MAX_TEMPERATURE:
                        response_text = response.text if hasattr(response, 'text') else ""
                        return {"role": "model", "content": response_text, "finish_reason": "RECITATION"}
                    else:
                        current_temperature += TEMPERATURE_INCREMENT
                        current_temperature = min(current_temperature, MAX_TEMPERATURE)
                        log.info(f"Recitation detected, retrying with temperature {current_temperature:.2f}")
                        continue

                # Extract response text
                response_text = ""
                if hasattr(response, 'text'):
                    response_text = response.text
                elif hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                response_text += part.text

                # Map finish reason
                mapped_reason = finish_reason
                if "STOP" in finish_reason.upper():
                    mapped_reason = "stop"
                elif "MAX_TOKENS" in finish_reason.upper():
                    mapped_reason = "length"

                return {
                    "role": "model",
                    "content": response_text,
                    "finish_reason": mapped_reason
                }

            except Exception as e:
                error_str = str(e).lower()
                # If thinking config caused the error, retry without it
                if not retry_without_thinking and ("thinking" in error_str or "budget" in error_str or "unsupported" in error_str):
                    log.warning(f"Thinking config not supported by model, retrying without: {e}")
                    retry_without_thinking = True
                    continue

                log.error(f"Error during Gemini generation: {e}")
                import traceback
                log.debug(traceback.format_exc())
                return {"role": "error", "content": f"Gemini API Error: {e}", "finish_reason": "error"}
