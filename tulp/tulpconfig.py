import os
import configparser
from . import tulpargs

CONFIG_FILE=os.path.expanduser("~/.tulp.conf")

class TulipConfig:
    _instance = None

    def getValue(self, key, defaultValue):
        value = self.config.get("DEFAULT", key, fallback=defaultValue)
        value = os.environ.get(f"TULP_{key}", value)
        return value

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)
            args = tulpargs.TulpArgs().get()
            cls._instance.config = configparser.ConfigParser()
            cls._instance.config.read(CONFIG_FILE)

            cls._instance.log_level = (args.v and "DEBUG") or (args.q and "ERROR")  or cls._instance.getValue("LOG_LEVEL", "INFO")
            cls._instance.openai_api_key = cls._instance.getValue("OPENAI_API_KEY",None)
            cls._instance.max_chars = int(args.max_chars or cls._instance.getValue("MAX_CHARS", "4000"))
            cls._instance.model = args.model or cls._instance.getValue("MODEL", "gpt-3.5-turbo")

        return cls._instance


