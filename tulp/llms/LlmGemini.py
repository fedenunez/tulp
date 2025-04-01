# tulp/llms/LlmGemini.py
import sys
from typing import List, Dict, Any, Optional
from ..logger import log
from ..config import TulpConfig
from .. import constants

# Conditional import for google-generativeai
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig
    # Import specific exceptions if available/needed
    # from google.api_core import exceptions as google_exceptions
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    HarmCategory = None
    HarmBlockThreshold = None
    GenerationConfig = None
    GEMINI_AVAILABLE = False
    # Warning logged during Client init or getModels/getArguments

# Gemini specific constants
SAFETY_SETTINGS_BLOCK_NONE = [
    {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
    {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_NONE},
    {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_NONE},
    {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
] if GEMINI_AVAILABLE else [] # Define empty if library missing

DEFAULT_TEMPERATURE = 1.0 # Gemini's default is often 0.9 or 1.0
MAX_TEMPERATURE = 2.0 # Check Gemini docs for actual max, might be 1.0 for some models
TEMPERATURE_INCREMENT = 0.33
REQUEST_TIMEOUT = 900 # seconds

def getModels() -> List[Dict[str, str]]:
   """Returns model definitions for Google Gemini."""
   if not GEMINI_AVAILABLE:
        log.warning("Google GenerativeAI library not found. Gemini models unavailable.")
        return []
   # Use raw string for regex
   return [ { "idRe": r"gemini.*", "description": "Any Google Gemini model (https://ai.google.dev/gemini-api/docs/models/gemini), requires GEMINI_API_KEY"} ]

def getArguments() -> List[Dict[str, Any]]:
   """Returns argument definitions specific to Gemini."""
   if not GEMINI_AVAILABLE:
        return []
   return [{"name": "gemini_api_key", "description": "Google AI (Gemini) API Key", "default": None}]


class Client:
    """Client for interacting with Google's Gemini models."""
    def __init__(self, config: TulpConfig):
        """Initializes the Gemini client."""
        self.config = config
        if not GEMINI_AVAILABLE:
            raise ImportError("Google GenerativeAI library is not installed. Cannot use Gemini client.")

        api_key = config.get_llm_argument("gemini_api_key")
        if not api_key:
            log.error(f'Gemini API key not found. Please set the {constants.ENV_VAR_PREFIX}GEMINI_API_KEY environment variable, add it to {config.config_file_path}, or use --gemini_api_key.')
            log.error("You can get a key at: https://aistudio.google.com/app/apikey")
            raise ValueError("Gemini API key is missing.")

        try:
            # Ensure genai is imported and configured
            assert genai is not None
            genai.configure(api_key=api_key)
            # Initialize model instance without system instruction initially
            # It will be re-initialized in generate() if a system prompt is present
            self.model_instance = genai.GenerativeModel(self.config.model)
            log.info("Gemini client initialized and configured.")
        except Exception as e:
            # Catch potential configuration errors or model validation issues
            log.error(f"Failed to initialize Gemini client or configure API key for model '{self.config.model}': {e}")
            # Provide more specific feedback if possible
            if "API key not valid" in str(e):
                 log.error("Please check if your Gemini API key is correct.")
            elif "permission denied" in str(e).lower():
                  log.error("Permission denied. Check API key permissions or project setup.")
            elif "model" in str(e).lower() and "not found" in str(e).lower():
                  log.error(f"Model '{self.config.model}' might not be available or name is incorrect.")

            raise ValueError(f"Gemini client initialization failed: {e}") from e

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Converts OpenAI message format to Gemini's Content format.
        Merges consecutive messages of the same role.
        Handles the constraint that messages cannot end with 'model'.
        Assumes system prompt is handled separately.
        """
        gemini_messages = []
        current_role: Optional[str] = None
        current_parts: List[str] = []

        # Gemini roles: 'user', 'model'
        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')

            # Map roles
            if role == 'assistant' or role == 'model':
                gemini_role = 'model'
            elif role == 'user':
                 gemini_role = 'user'
            else:
                 # Treat unexpected roles (like system after first) as user
                 log.warning(f"Treating unexpected role '{role}' as 'user' for Gemini.")
                 gemini_role = 'user'

            if current_role is None:
                current_role = gemini_role
                current_parts = [content]
            elif gemini_role == current_role:
                # Merge content for the same role
                current_parts.append(content)
            else:
                # Role changed, finalize previous block
                if current_role and current_parts:
                    # Join parts, filtering empty ones
                    joined_content = "\n".join(filter(None, current_parts))
                    if joined_content or current_role == 'model': # Allow empty model messages? Check Gemini docs. Assume no for now.
                         if joined_content:
                              gemini_messages.append({'role': current_role, 'parts': [joined_content]}) # Gemini expects parts as list of strings
                # Start new block
                current_role = gemini_role
                current_parts = [content]

        # Append the last message block
        if current_role and current_parts:
             joined_content = "\n".join(filter(None, current_parts))
             if joined_content:
                  gemini_messages.append({'role': current_role, 'parts': [joined_content]})

        # Gemini validation: Cannot end with 'model' role.
        if gemini_messages and gemini_messages[-1]['role'] == 'model':
            log.warning("Gemini doesn't allow conversation history to end with 'model' role. Appending a placeholder 'user' message.")
            # Append a minimal, likely ignored user message.
            gemini_messages.append({'role': 'user', 'parts': ["(Continue)"]}) # Placeholder

        log.debug(f"Converted messages for Gemini history: {len(gemini_messages)} messages")
        return gemini_messages

    def generate(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generates a response from the Gemini model."""
        if not GEMINI_AVAILABLE:
            return {"role": "error", "content": "Google GenerativeAI library not installed.", "finish_reason": "error"}

        # Handle system prompt if present
        system_instruction: Optional[str] = None
        openai_msgs_to_process = messages
        if messages and messages[0]['role'] == 'system':
            system_instruction = messages[0]['content']
            openai_msgs_to_process = messages[1:]
            log.debug("Using first message content as Gemini system instruction.")
            # Re-initialize model with system instruction
            try:
                # Ensure necessary imports are available
                assert genai is not None
                self.model_instance = genai.GenerativeModel(self.config.model, system_instruction=system_instruction)
            except Exception as e:
                log.error(f"Failed to re-initialize Gemini model with system instruction: {e}")
                # Fallback to model without system instruction? Or fail? Let's fail.
                return {"role": "error", "content": f"Failed to set system instruction: {e}", "finish_reason": "error"}

        gemini_history = self._convert_messages(openai_msgs_to_process)

        # The actual prompt to generate content from is the last user message (implicitly)
        # Gemini's generate_content takes the full history.

        if not gemini_history:
             log.error("Cannot send empty message history to Gemini.")
             return {"role": "error", "content": "Empty message history.", "finish_reason": "error"}

        current_temperature = DEFAULT_TEMPERATURE
        # Ensure GenerationConfig is available
        assert GenerationConfig is not None
        generation_config = GenerationConfig(
            candidate_count=1,
            temperature=current_temperature
            # Consider adding max_output_tokens from config if available
            # max_output_tokens=self.config.max_output_tokens or 8192 # Example
        )

        while True: # Loop for retrying on recitation
            log.debug(f"Sending request to Gemini model {self.config.model} with temp {current_temperature:.2f}...")
            try:
                # Ensure model_instance is valid
                assert self.model_instance is not None
                response = self.model_instance.generate_content(
                    gemini_history, # Pass the converted history
                    safety_settings=SAFETY_SETTINGS_BLOCK_NONE,
                    request_options={"timeout": REQUEST_TIMEOUT},
                    generation_config=generation_config
                )
                # Log the raw response for debugging if needed (can be large)
                # log.debug(f"Gemini raw response: {response}")

                # --- Process Response ---
                # Check for prompt feedback first (indicates blocks before generation)
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    block_reason = response.prompt_feedback.block_reason.name
                    log.error(f"Gemini prompt blocked before generation. Reason: {block_reason}")
                    ratings_str = ", ".join([f"{r.category.name}: {r.probability.name}" for r in response.prompt_feedback.safety_ratings])
                    log.error(f"Prompt Safety Ratings: {ratings_str}")
                    return {"role": "error", "content": f"Blocked by Gemini (Prompt): {block_reason}", "finish_reason": "SAFETY"}


                # Check candidates and safety ratings
                if not response.candidates:
                     log.error("Gemini response contained no candidates.")
                     # This might also indicate a block, check prompt feedback again just in case
                     block_reason = response.prompt_feedback.block_reason.name if response.prompt_feedback else 'UNKNOWN'
                     return {"role": "error", "content": f"Gemini returned no candidates (Block Reason: {block_reason})", "finish_reason": "error"} # Or map reason

                candidate = response.candidates[0]
                finish_reason_enum = candidate.finish_reason
                finish_reason = finish_reason_enum.name # Get the string name

                # Handle safety blocks on the *response*
                if finish_reason == "SAFETY":
                     safety_ratings_str = ", ".join([f"{r.category.name}: {r.probability.name}" for r in candidate.safety_ratings])
                     log.error(f"Gemini response blocked due to safety settings. Ratings: {safety_ratings_str}")
                     return {"role": "error", "content": "Blocked by Gemini Safety Filter (Response)", "finish_reason": "SAFETY"}

                # Handle recitation
                if finish_reason == "RECITATION":
                    log.warning("Gemini response flagged for recitation.")
                    if current_temperature >= MAX_TEMPERATURE:
                        log.error(f"Max temperature ({MAX_TEMPERATURE:.2f}) reached, still getting recitation. Giving up.")
                        # Return the (potentially empty or partial) content along with the reason
                        response_text = candidate.content.parts[0].text if candidate.content.parts else ""
                        return {"role": candidate.content.role, "content": response_text, "finish_reason": "RECITATION"}
                    else:
                        current_temperature += TEMPERATURE_INCREMENT
                        current_temperature = min(current_temperature, MAX_TEMPERATURE) # Cap temperature
                        log.info(f"Retrying with increased temperature: {current_temperature:.2f}")
                        generation_config.temperature = current_temperature # Update config for next try
                        continue # Retry the loop

                # --- Successful Response or other non-retryable finish ---
                response_role = candidate.content.role # Should be 'model'
                # Handle potential missing parts or non-text parts
                response_text = ""
                if candidate.content.parts:
                    # Assuming the first part is the text we want
                     if hasattr(candidate.content.parts[0], 'text'):
                          response_text = candidate.content.parts[0].text
                     else:
                          log.warning(f"First part of Gemini response is not text: {candidate.content.parts[0]}")
                else:
                     log.warning("Gemini response candidate content has no parts.")


                log.debug(f"Gemini finish reason: {finish_reason}")

                # Map finish reasons if desired
                mapped_reason = finish_reason
                if finish_reason == "STOP": mapped_reason = "stop"
                elif finish_reason == "MAX_TOKENS": mapped_reason = "length"
                # Other reasons: SAFETY, RECITATION, OTHER

                return {
                    "role": response_role,
                    "content": response_text,
                    "finish_reason": mapped_reason # Return mapped reason
                }

            # Handle potential API errors during the request
            except Exception as e:
                # Catch potential google API errors if possible
                # Example:
                # if isinstance(e, google_exceptions.GoogleAPIError):
                #     log.error(f"Google API Error: {e}")
                #     return {"role": "error", "content": f"Google API Error: {e}", "finish_reason": "error"}

                log.error(f"Error during Gemini generation: {e}")
                import traceback
                log.debug(traceback.format_exc())
                return {"role": "error", "content": f"Gemini API Error: {e}", "finish_reason": "error"}
            # Break loop if not retrying (i.e., response was processed or error occurred)
            break
