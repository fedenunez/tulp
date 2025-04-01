# promptSerializer.py
import json
import os
from .logger import log
from typing import List, Dict, Any, Optional # Added Optional

class RequestMessageSerializer:
    """Saves and loads conversation histories (request/response) to JSON files."""

    def __init__(self, filename: str):
        """
        Initializes the serializer with a target filename.
        Ensures the directory for the file exists.
        """
        self.filename = os.path.abspath(filename) # Store full path
        # Ensure directory exists
        try:
            dir_name = os.path.dirname(self.filename)
            if dir_name: # Avoid trying to create '' if filename is in current dir
                os.makedirs(dir_name, exist_ok=True)
        except OSError as e:
            # Log warning but don't prevent instantiation; saving will fail later.
            log.warning(f"Could not create directory '{os.path.dirname(self.filename)}' for saving: {e}")


    def save(self, request_messages: List[Dict[str, Any]], response: Optional[Dict[str, Any]] = None):
        """
        Saves the list of messages to the instance's filename.
        If a response object is provided, it's temporarily appended for saving.

        Args:
            request_messages: The list of request messages (history).
            response: The optional final response message from the LLM.
        """
        messages_to_save = list(request_messages) # Create a copy to avoid modifying original list
        if response:
            # Ensure response is a dictionary before appending
            if isinstance(response, dict):
                messages_to_save.append(response)
            else:
                 log.warning(f"Invalid response type provided to save method: {type(response)}. Expected dict.")

        try:
            with open(self.filename, 'w', encoding='utf-8') as file:
                json.dump(messages_to_save, file, indent=2, ensure_ascii=False)
            log.debug(f"Saved conversation ({len(messages_to_save)} messages) to {self.filename}")
        except IOError as e:
            log.error(f"Failed to write conversation to {self.filename}: {e}")
        except TypeError as e:
             log.error(f"Failed to serialize conversation to JSON for {self.filename}: {e}")


    def load(self) -> Optional[List[Dict[str, Any]]]:
        """Loads conversation messages from the instance's JSON file."""
        if not os.path.exists(self.filename):
             log.error(f"Conversation file not found: {self.filename}")
             return None
        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                messages = json.load(file)
                if not isinstance(messages, list):
                     log.error(f"File {self.filename} does not contain a valid JSON list.")
                     return None
                log.debug(f"Loaded conversation ({len(messages)} messages) from {self.filename}")
                return messages
        except json.JSONDecodeError as e:
            log.error(f"Failed to decode JSON from {self.filename}: {e}")
            return None
        except IOError as e:
            log.error(f"Failed to read conversation file {self.filename}: {e}")
            return None
        except Exception as e:
             log.error(f"Unexpected error loading conversation from {self.filename}: {e}")
             return None

    # getMessage method from original code seems unused or unclear.
    # It returned only the first message found. Removing it for clarity.
    # If specific message retrieval is needed, add methods like get_last_message, etc.
    # def getMessage(self):
    #     messages = self.load()
    #     for message in messages: # This loop only ever returned the first item
    #         return message
    #     return None

