import sys
from .. import tulplogger
log = tulplogger.Logger()


def getModels():
   return [ { "idRe":"ollama.*", "description":  "Any ollama model with the prefix 'ollama', the model should be running in the ollama_host."} ]

def getArguments():
    return [{"name": "ollama_host", "description": "Define custom ollama host, by default it will connect to http://127.0.0.1:11434", "default":"http://127.0.0.1:11434"}]



class Client:
    def __init__(self,config):
        self.config = config
        ollama_host = config.ollama_host
        from ollama import Client
        self.client = Client(host=ollama_host)
        
    def getModel(self):
        return self.config.model.lstrip("ollama.")


    def convertMessagesFromOpenAI(self, messages):
        gmessages = []
        pRole = None
        pParts = None
        for msg in messages:
            cRole = (msg['role'] == "assistant" and "assistant" or "user")
            if pRole and cRole != pRole:
               gmessages.append( {'role': pRole , 'content': "\n".join(pParts) } )
               pRole = None
            if not pRole:
                pRole = cRole
                pParts = [msg['content']]
            else:
                pParts.append(msg['content'])
        # append the pending messages
        if pRole:
               gmessages.append( {'role': pRole , 'content': "\n".join(pParts) } )

        return gmessages

    def generate(self, messages):
        pmsgs = self.convertMessagesFromOpenAI(messages)
        for req in pmsgs:
            log.debug(f"REQ: {req}")
        log.debug(f"Sending the request to llm...")
        response = self.client.chat(
                model=self.getModel(),
                messages=pmsgs,
                )
        log.debug(f"ANS: {response}")
# [DEBUG] Sending the request to llm...
# [DEBUG] ANS: {'model': 'phi3:instruct', 'created_at': '2024-05-03T14:57:07.682604174Z', 'message': {'role': 'assistant', 'content': "(#output)\nfind / -name 'mylovelyfile' # This command will search for a file named 'mylovelyfile' starting from root directory. Remember to replace '/' with your specific path if needed and ensure you have appropriate permissions, as this operation can potentially access many files across the system.\n(#comment)"}, 'done': True, 'total_duration': 252355913064, 'load_duration': 3772635741, 'prompt_eval_count': 818, 'prompt_eval_duration': 224214833000, 'eval_count': 71, 'eval_duration': 24218315000}

# TODO: Check finish reason, we need to comply with openAI api:#Every response will include a finish_reason. The possible values for finish_reason are:
# 
# stop: API returned complete message, or a message terminated by one of the stop sequences provided via the stop parameter
# length: Incomplete model output due to max_tokens parameter or token limit
# function_call: The model decided to call a function
# content_filter: Omitted content due to a flag from our content filters
# null: API response still in progress or incomplete
        return { 
                "role": response['message']['role'],
                "content": response['message']['content'],
                "finish_reason": response['done']
               }
