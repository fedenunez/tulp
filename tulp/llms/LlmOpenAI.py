
import sys
from openai import OpenAI
from .. import tulplogger
log = tulplogger.Logger()


# List all Models first

def getModels():
    return [ { "idRe":"(gpt-|chatgpt-|openai.).*", "description":  "Any OpenAI model (https://platform.openai.com/docs/models) requires the definition of an openai_api_key. It will support most model names directly (like gpt-4), or you can use openai.<MODEL_NAME> to use any unsupported model, like openai.o1." } ]


def getArguments():
    return [{"name": "openai_api_key", "description": "OpenAI cloud API KEY", "default":None},
            {"name": "openai_baseurl", "description": "Use it to change the server, e.g.: use http://localhost:11434/v1/ to connect to your local ollama server", "default": None} ]



class Client:
    def __init__(self,config):
        self.config = config
        openai_key = config.openai_api_key
        if not openai_key:
            log.error(f'OpenAI API key not found. Please set the TULP_OPENAI_API_KEY environment variable or add it to {config.CONFIG_FILE()}')
            log.error(f"If you don't have one, please create one at: https://platform.openai.com/account/api-keys")
            sys.exit(1)
        if config.openai_baseurl:
            self.client = OpenAI(base_url=config.openai_baseurl, api_key=openai_key)
        else:
            self.client = OpenAI(api_key=openai_key)

    def getModel(self):
        return self.config.model[7:] if self.config.model.startswith("openai.") else self.config.model

    def generate(self, messages):
        """
        Writes the given content to the given file name. If the file already exists, it will rename it to a new file on the same folder, appending to the file name a counter (like -1) and keeping the same extension. It will continually increase the counter until it finds a free object.

        :param file_name: The name of the file to write to.
        """

        for req in messages:
            log.debug(f"REQ: {req}")
        log.debug(f"Sending the request to llm...")
        response = self.client.chat.completions.create(model=self.getModel(),
        messages=messages,
        temperature=0)
        log.debug(f"ANS: {response}")
        return { 
                "role": response.choices[0].message.role,
                "content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason
               }
