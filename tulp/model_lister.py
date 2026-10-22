# model_lister.py
"""
`--list-models`: asks each configured provider which models it serves.

Every provider Client implements `list_models() -> List[str]` (raw provider model ids).
This module turns them into names usable with `-m` (adding the provider prefix when the
raw id would not route back to that provider), drops non-text models, and prints them.
"""
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Tuple

from . import llms
from .logger import log

# Models tulp can't use for text generation (embeddings, speech, images, video, safety classifiers...)
NON_TEXT_MODEL_RE = re.compile(
    r"embed|tts|whisper|transcri|realtime|audio|image|dall-e|moderation|guard|orpheus|veo|imagen|"
    r"lyria|robotics|computer-use|-live|sora|babbage|davinci|search|aqa|nano-banana|deep-research|translate",
    re.IGNORECASE,
)


def provider_name(module: Any) -> str:
    """Short provider id from the module name: LlmOpenAI -> openai, LlmZai -> zai."""
    return module.__name__.rsplit(".", 1)[-1][len("Llm"):].lower()


def provider_names() -> List[str]:
    """Short ids of every loaded provider, sorted."""
    return sorted(provider_name(m) for m in llms.get_modules())


def _missing_credentials(module: Any, config: Any) -> List[str]:
    """API-key arguments of the module that are unset (empty if it needs none or one is set)."""
    arg_names = [a["name"] for a in module.getArguments()]
    key_args = [n for n in arg_names if n.endswith("_api_key")]
    if not key_args or any(config.get_llm_argument(n) for n in key_args):
        return []
    # OpenAI-compatible local endpoints (e.g. --openai-baseurl http://localhost...) need no key
    if any(config.get_llm_argument(n) for n in arg_names if n.endswith("_baseurl")):
        return []
    return key_args


def to_tulp_name(module: Any, model_id: str) -> str | None:
    """Maps a provider model id to a `-m` name that routes back to `module`, or None."""
    if llms.get_model_module(model_id) is module:
        return model_id
    prefix = getattr(module.Client, "MODEL_PREFIX", "")
    if prefix and llms.get_model_module(prefix + model_id) is module:
        return prefix + model_id
    return None  # e.g. Gemini's gemma-* models: tulp only routes gemini-* to Gemini


def _list_provider(module: Any, config: Any) -> Tuple[str, List[str] | None, str]:
    """Returns (provider, tulp model names or None, status message)."""
    name = provider_name(module)
    missing = _missing_credentials(module, config)
    if missing:
        env_vars = ", ".join(f"TULP_{n.upper()}" for n in missing)
        return name, None, f"skipped: no API key (set {env_vars} or the config file)"
    try:
        client = module.Client(config)
        model_ids = client.list_models()
    except Exception as e:  # pylint: disable=broad-except
        return name, None, f"failed: {e}"
    names = sorted({tulp_name for model_id in model_ids if not NON_TEXT_MODEL_RE.search(model_id)
                    for tulp_name in [to_tulp_name(module, model_id)] if tulp_name})
    return name, names, f"{len(names)} models"


def list_models(provider: str, config: Any) -> int:
    """Prints available models (all providers, or one). Returns the process exit code."""
    modules = llms.get_modules()
    if provider != "all":
        modules = [m for m in modules if provider_name(m) == provider.lower()]
        if not modules:
            log.error(f"Unknown provider '{provider}'. Choose one of: {', '.join(provider_names())}")
            return 2

    # Providers are queried in parallel; each SDK call has its own network timeout.
    with ThreadPoolExecutor(max_workers=len(modules)) as pool:
        results = list(pool.map(lambda m: _list_provider(m, config), modules))

    listed: Dict[str, List[str]] = {}
    for name, names, status in sorted(results):
        if names is None:
            log.warning(f"{name}: {status}")
        else:
            log.info(f"{name}: {status}")
            listed[name] = names
    sys.stderr.flush()

    for name, names in sorted(listed.items()):
        print(f"# {name}")
        for model_name in names:
            print(model_name)
    sys.stdout.flush()
    return 0 if listed else 1
