"""Offline tests for provider routing and request building (no API calls)."""
from types import SimpleNamespace

import pytest

from tulp import llms
from tulp.llms import LlmAnthropic, LlmDeepSeek, LlmGemini, LlmOpenAI, LlmZai


def make_config(model, thinking_level="low", **llm_args):
    """Minimal stand-in for TulpConfig with only what the clients read."""
    return SimpleNamespace(
        model=model,
        thinking_level=thinking_level,
        config_file_path="~/.tulp.conf",
        get_llm_argument=llm_args.get,
    )


@pytest.mark.parametrize("model, module", [
    ("gpt-6-luna", LlmOpenAI),
    ("gpt-6.1-sol", LlmOpenAI),
    ("gemini-4-argon", LlmGemini),
    ("claude-opus-5-5", LlmAnthropic),
    ("deepseek-flash", LlmDeepSeek),
    ("deepseek-v4-pro", LlmDeepSeek),
    ("glm-5.3", LlmZai),
    ("zai.some-new-model", LlmZai),
])
def test_model_routing(model, module):
    assert llms.get_model_module(model) is module


@pytest.mark.parametrize("model, adaptive", [
    ("claude-opus-5-5", True),
    ("claude-sonnet-5-5", True),
    ("claude-haiku-5-5", True),
    ("claude-sonnet-5", True),
    ("claude-fable-5-1", True),
    ("claude-opus-4-6", True),
    ("claude-opus-4-8", True),
    ("claude-haiku-4-5", False),
    ("claude-haiku-4-5-20251001", False),
    ("claude-sonnet-4-20250514", False),
    ("claude-opus-4-1", False),
    ("claude-3-7-sonnet-20250219", False),
    ("claude-3-opus-20240229", False),
])
def test_anthropic_thinking_mode(model, adaptive):
    assert LlmAnthropic.Client._uses_adaptive_thinking(model) is adaptive


def test_anthropic_adaptive_request():
    client = LlmAnthropic.Client(make_config("claude-opus-5-5", "medium", anthropic_api_key="dummy"))
    kwargs = client._build_request([{"role": "user", "content": "hi"}], "sys")
    assert kwargs["thinking"] == {"type": "adaptive"}
    assert kwargs["output_config"] == {"effort": "medium"}
    assert kwargs["system"] == "sys"
    assert not {"temperature", "top_p", "top_k"} & kwargs.keys()


def test_anthropic_legacy_request():
    client = LlmAnthropic.Client(make_config("claude-haiku-4-5", "low", anthropic_api_key="dummy"))
    kwargs = client._build_request([{"role": "user", "content": "hi"}], None)
    assert kwargs["thinking"] == {"type": "enabled", "budget_tokens": 2048}
    assert kwargs["max_tokens"] > 2048
    assert "output_config" not in kwargs
    assert "system" not in kwargs


def test_deepseek_request_params():
    client = LlmDeepSeek.Client(make_config("deepseek-flash", "high", deepseek_api_key="dummy"))
    assert str(client.client.base_url).startswith("https://api.deepseek.com")
    params = client._extra_params("deepseek-flash")
    assert params["extra_body"] == {"thinking": {"type": "enabled"}, "reasoning_effort": "high"}


def test_zai_prefix_and_baseurl_override():
    client = LlmZai.Client(make_config("zai.glm-x", zai_api_key="dummy",
                                       zai_baseurl=LlmZai.Client.CODING_PLAN_BASEURL))
    assert client._get_model_name() == "glm-x"
    assert "coding" in str(client.client.base_url)


def test_missing_api_key_raises():
    with pytest.raises(ValueError):
        LlmDeepSeek.Client(make_config("deepseek-flash"))


def test_continuation_messages_are_cleaned():
    cleaned = LlmZai.Client._clean_messages(
        [{"role": "assistant", "content": "x", "finish_reason": "length"}])
    assert cleaned == [{"role": "assistant", "content": "x"}]


@pytest.mark.parametrize("model, responses_api, reasoning", [
    ("gpt-6-luna", True, True),
    ("gpt-6.1-sol", True, True),
    ("gpt-5.6-terra", True, True),
    ("gpt-5-mini", True, True),
    ("gpt-5-chat-latest", True, False),
    ("gpt-4.1", True, False),
    ("gpt-4o", False, False),
    ("o3", False, True),
])
def test_openai_routing(model, responses_api, reasoning):
    client = LlmOpenAI.Client(make_config(model, openai_api_key="dummy"))
    assert client._should_use_responses_api(model) is responses_api
    assert client._is_reasoning_model(model) is reasoning


@pytest.mark.parametrize("model, thinking", [
    ("gemini-4-argon", True),
    ("gemini-3.8-flash", True),
    ("gemini-2.5-flash", True),
    ("gemini-2.0-flash", False),
    ("gemini-flash-latest", True),
])
def test_gemini_thinking_detection(model, thinking):
    client = LlmGemini.Client(make_config(model, gemini_api_key="dummy"))
    assert client._is_thinking_model() is thinking


def test_startup_does_not_import_provider_sdks():
    """`tulp -h` must stay fast: SDKs (seconds to import) load only on first Client()."""
    import subprocess  # pylint: disable=import-outside-toplevel
    import sys  # pylint: disable=import-outside-toplevel
    code = ("import sys, tulp.cli, tulp.llms; tulp.llms.get_models_definitions(); "
            "print([m for m in ('openai', 'anthropic', 'groq', 'ollama', 'google.genai') if m in sys.modules])")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout
    assert out.strip() == "[]"


@pytest.mark.parametrize("module, model_id, expected", [
    (LlmOpenAI, "gpt-6-luna", "gpt-6-luna"),
    (LlmOpenAI, "o4-mini", "openai.o4-mini"),
    (LlmZai, "glm-5.3", "glm-5.3"),
    (LlmGemini, "gemma-3-27b-it", None),
])
def test_list_models_tulp_names(module, model_id, expected):
    from tulp import model_lister  # pylint: disable=import-outside-toplevel
    assert model_lister.to_tulp_name(module, model_id) == expected


def test_list_models_output(monkeypatch, capsys):
    from tulp import llms as llms_pkg, model_lister  # pylint: disable=import-outside-toplevel
    from tulp.llms import LlmGroq, LlmOllama  # pylint: disable=import-outside-toplevel

    class FakeClient:
        """Stands in for a provider client; returns canned raw model ids."""
        MODEL_PREFIX = ""
        IDS = []

        def __init__(self, config):
            self.config = config

        def list_models(self):
            return self.IDS

    def fake(module, ids, prefix=""):
        cls = type(f"Fake{module.__name__}", (FakeClient,), {"IDS": ids, "MODEL_PREFIX": prefix})
        monkeypatch.setattr(module, "Client", cls)

    fake(LlmOpenAI, ["gpt-6-luna", "text-embedding-3-large", "gpt-image-2", "o4-mini"], "openai.")
    fake(LlmGroq, ["openai/gpt-oss-120b", "whisper-large-v3"], "groq.")
    monkeypatch.setattr(llms_pkg, "get_modules", lambda: [LlmOpenAI, LlmGroq, LlmOllama])
    fake(LlmOllama, [])
    monkeypatch.setattr(LlmOllama.Client, "list_models", lambda self: (_ for _ in ()).throw(ConnectionError("down")))
    config = make_config("x", openai_api_key="k", groq_api_key="k")

    assert model_lister.list_models("all", config) == 0
    out = capsys.readouterr().out.splitlines()
    assert out == ["# groq", "groq.openai/gpt-oss-120b", "# openai", "gpt-6-luna", "openai.o4-mini"]

    assert model_lister.list_models("anthropic", make_config("x")) == 2  # unknown: not among the loaded modules


def test_config_duplicate_keys_last_wins(tmp_path):
    """A key repeated in ~/.tulp.conf must not discard the file: the last value wins."""
    import subprocess  # pylint: disable=import-outside-toplevel
    import sys  # pylint: disable=import-outside-toplevel
    (tmp_path / ".tulp.conf").write_text(
        "[DEFAULT]\nANTHROPIC_API_KEY = first\nDEEPSEEK_API_KEY = ds\nANTHROPIC_API_KEY = last\n")
    code = ("import sys; sys.argv = ['tulp', 'hi']\n"
            "from tulp import arguments\n"
            "from tulp.config import initialize_config, get_config\n"
            "initialize_config(arguments.get_args()); c = get_config()\n"
            "print(c.get_llm_argument('anthropic_api_key'), c.get_llm_argument('deepseek_api_key'))")
    env = {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True, env=env)
    assert result.stdout.split() == ["last", "ds"]
    assert "ERROR" not in result.stderr
