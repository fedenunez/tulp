import os
import configparser
from . import tulpargs
from . import tulplogger

CONFIG_FILE=os.path.expanduser("~/.tulp.conf")

class TulipConfig:
    _instance = None

    def getValue(self, key, defaultValue):
        value = self.config.get("DEFAULT", key, fallback=defaultValue)
        value = os.environ.get(f"TULP_{key}", value)
        return value

    def CONFIG_FILE(self):
        return CONFIG_FILE
    def loadLlmsArguments(self,cliargs):
        from . import llms
        for o in llms.getArguments():
            setattr(self,o['name'], cliargs.__getattribute__(o["name"]) or self.getValue(o["name"].upper(),o["default"]))

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)
            args = tulpargs.TulpArgs().get()
            cls._instance.config = configparser.ConfigParser()
            cls._instance.config.read(CONFIG_FILE)


            cls._instance.log_level = (args.v and "DEBUG") or (args.q and "ERROR")  or cls._instance.getValue("LOG_LEVEL", "INFO")
            tulplogger.setLogLevel(cls._instance.log_level)
            cls._instance.max_chars = int(args.max_chars or cls._instance.getValue("MAX_CHARS", "1000000"))
            cls._instance.model = args.model or cls._instance.getValue("MODEL", "gpt-4o")
            cls._instance.loadLlmsArguments(args)

        return cls._instance


