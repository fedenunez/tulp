# llms/__init__.py
import os
import sys
import importlib
import re
from typing import List, Dict, Any, Type, TYPE_CHECKING
from ..logger import log

# Use TYPE_CHECKING to avoid circular import for type hints
if TYPE_CHECKING:
    from ..config import TulpConfig # Import for type hinting config object
    # Define a base client type if you create one, otherwise use Any
    # class BaseLlmClient: ...
    LlmClientType = Any


# --- Module Loading ---

_llm_modules = []
_arguments_definitions: List[Dict[str, Any]] | None = None # Type hint for clarity
_models_definitions: List[Dict[str, Any]] | None = None # Type hint for clarity

def _load_modules():
    """Dynamically loads LLM provider modules from the current directory."""
    global _llm_modules
    if _llm_modules: # Already loaded
        return

    current_dir = os.path.dirname(__file__)
    log.debug(f"Loading LLM modules from: {current_dir}")
    loaded_module_names = set() # Track names to avoid duplicates if structure changes

    for filename in os.listdir(current_dir):
        # Look for files starting with Llm and ending with .py
        if filename.endswith(".py") and filename != "__init__.py" and filename.startswith("Llm"):
            module_name = filename[:-3]  # Remove .py
            if module_name in loaded_module_names:
                continue # Skip if already loaded

            try:
                # Use relative import within the package
                module = importlib.import_module(f".{module_name}", package=__name__)
                # Check for required components
                if hasattr(module, 'Client') and callable(getattr(module, 'Client')) and \
                   hasattr(module, 'getArguments') and callable(getattr(module, 'getArguments')) and \
                   hasattr(module, 'getModels') and callable(getattr(module, 'getModels')):
                    _llm_modules.append(module)
                    loaded_module_names.add(module_name)
                    log.debug(f"Successfully loaded LLM module: {module_name}")
                else:
                    missing = []
                    if not (hasattr(module, 'Client') and callable(getattr(module, 'Client'))): missing.append('Client class')
                    if not (hasattr(module, 'getArguments') and callable(getattr(module, 'getArguments'))): missing.append('getArguments function')
                    if not (hasattr(module, 'getModels') and callable(getattr(module, 'getModels'))): missing.append('getModels function')
                    log.warning(f"Skipping module '{module_name}': Missing or invalid components: {', '.join(missing)}.")
            except ImportError as e:
                log.error(f"Failed to import LLM module '{module_name}': {e}")
            except Exception as e:
                 log.error(f"Unexpected error loading LLM module '{module_name}': {e}")

_load_modules() # Load modules when this package is imported

# --- Public API ---

def get_arguments_definitions() -> List[Dict[str, Any]]:
    """
    Gets a list of argument definitions from all loaded LLM modules.
    Format: [{'name': str, 'description': str, 'default': Any}, ...]
    Caches the result after the first call.
    """
    global _arguments_definitions
    if _arguments_definitions is None:
        _arguments_definitions = []
        log.debug("Collecting LLM argument definitions...")
        for module in _llm_modules:
            try:
                args = module.getArguments()
                # Basic validation
                if isinstance(args, list) and all(isinstance(d, dict) and 'name' in d for d in args):
                    _arguments_definitions.extend(args)
                else:
                    log.warning(f"Module {module.__name__} getArguments() did not return a valid list of dicts.")
            except Exception as e:
                log.error(f"Error getting arguments from {module.__name__}: {e}")
        log.debug(f"Collected {len(_arguments_definitions)} LLM argument definitions.")
    return _arguments_definitions

def get_models_definitions() -> List[Dict[str, Any]]:
    """
    Gets a list of model definitions from all loaded LLM modules.
    Adds a reference to the module itself in each definition.
    Format: [{'idRe': str, 'description': str, 'module': module}, ...]
    Caches the result after the first call.
    """
    global _models_definitions
    if _models_definitions is None:
        _models_definitions = []
        log.debug("Collecting LLM model definitions...")
        for module in _llm_modules:
            try:
                models = module.getModels()
                 # Basic validation
                if isinstance(models, list) and all(isinstance(d, dict) and 'idRe' in d for d in models):
                    for model_def in models:
                        if 'module' not in model_def: # Avoid overwriting if already set somehow
                             model_def['module'] = module # Add reference to the module
                        _models_definitions.append(model_def)
                else:
                    log.warning(f"Module {module.__name__} getModels() did not return a valid list of dicts.")
            except Exception as e:
                log.error(f"Error getting models from {module.__name__}: {e}")
        log.debug(f"Collected {len(_models_definitions)} LLM model definitions.")
    return _models_definitions

def get_models_description() -> str:
    """Generates a formatted string describing all available models."""
    definitions = get_models_definitions() # Ensure definitions are loaded
    if not definitions:
        return "   No models found or loaded."

    descriptions = []
    for model_def in definitions:
        # Ensure required keys exist before formatting
        id_re = model_def.get('idRe', '<missing_regex>')
        desc = model_def.get('description', '<missing_description>')
        descriptions.append(f"   - {id_re} : {desc}")
    return "\n".join(descriptions)

def get_model_module(model_name: str) -> Any | None:
    """Finds the LLM provider module corresponding to a given model name via regex matching."""
    definitions = get_models_definitions() # Ensure definitions are loaded
    log.debug(f"Searching for module matching model name: '{model_name}'")
    for model_def in definitions:
        regex_pattern = model_def.get("idRe")
        module = model_def.get("module")
        if not regex_pattern or not module:
             log.warning(f"Skipping invalid model definition: {model_def}")
             continue
        try:
            # Use fullmatch for potentially more precise matching if needed, or match for prefix
            # Let's stick with match as per original logic (prefix or pattern match)
            if re.match(regex_pattern, model_name):
                log.debug(f"Model '{model_name}' matched regex '{regex_pattern}' from module {module.__name__}")
                return module
        except re.error as e:
            log.error(f"Invalid regex '{regex_pattern}' in {module.__name__}: {e}")
            # Continue searching other definitions despite the error
        except Exception as e:
             log.error(f"Error during regex matching for pattern '{regex_pattern}': {e}")

    log.debug(f"No module found matching model name: {model_name}")
    return None

def get_model_client(model_name: str, config: 'TulpConfig') -> 'LlmClientType':
    """
    Instantiates and returns the LLM Client class from the appropriate module.

    Args:
        model_name: The name of the model (e.g., "gpt-4o", "groq.llama3-70b-8192").
        config: The TulpConfig object containing necessary configurations (API keys, etc.).

    Returns:
        An instance of the corresponding LLM client class (e.g., LlmOpenAI.Client).

    Raises:
        ValueError: If no module is found for the model name or instantiation fails.
        AttributeError: If the found module doesn't have a callable 'Client' class.
        ImportError: If a required library for the client is missing.
    """
    module = get_model_module(model_name)
    if module:
        if hasattr(module, 'Client') and callable(getattr(module, 'Client')):
            try:
                log.info(f"Instantiating client for model '{model_name}' using module {module.__name__}")
                # The Client class __init__ expects the config object
                client_instance = module.Client(config)
                return client_instance
            except ImportError as ie:
                 # Catch missing libraries specific to the client here
                 log.error(f"Missing dependency required by {module.__name__} for model '{model_name}': {ie}")
                 raise # Re-raise ImportError for cli.py to handle
            except ValueError as ve:
                 # Catch configuration errors like missing API keys raised by client __init__
                 log.error(f"Configuration error initializing client from {module.__name__}: {ve}")
                 raise # Re-raise ValueError
            except Exception as e:
                log.error(f"Failed to instantiate client from {module.__name__} for model '{model_name}': {e}")
                # Wrap unexpected errors in a ValueError for consistent handling?
                raise ValueError(f"Client instantiation failed for {model_name}") from e
        else:
            raise AttributeError(f"Module {module.__name__} found for model '{model_name}', but it lacks a callable 'Client' class.")
    else:
        # This case should ideally be caught by argument validation first, but double-check
        raise ValueError(f"No LLM provider module found matching model name: '{model_name}'")
