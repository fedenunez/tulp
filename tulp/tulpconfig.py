import os
import configparser

CONFIG_FILE=os.path.expanduser("~/.tulp.conf")

class TulipConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config = configparser.ConfigParser()
            cls._instance.config.read(CONFIG_FILE)
            cls._instance.log_level = os.environ.get("TULP_LOG_LEVEL", cls._instance.config.get("DEFAULT", "LOG_LEVEL", fallback="INFO"))
            cls._instance.openai_api_key = os.environ.get("TULP_OPENAI_API_KEY",
                    os.environ.get("OPENAI_API_KEY", cls._instance.config.get("DEFAULT", "OPENAI_API_KEY", fallback=""))
                    )
            cls._instance.max_chars = int(os.environ.get("TULP_MAX_CHARS", cls._instance.config.get("DEFAULT", "MAX_CHARS", fallback="4000")))
            cls._instance.model = os.environ.get("TULP_MODEL", cls._instance.config.get("DEFAULT", "MODEL", fallback="gpt-3.5-turbo"))
        return cls._instance
