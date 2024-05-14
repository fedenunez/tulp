import anthropic
import sys
from .. import tulplogger
log = tulplogger.Logger()


def getModels():
   return [ { "idRe":"claude-.*", "description":  "Any Anthropic claude model (https://docs.anthropic.com/claude/docs/models-overview), requires ANTHROPIC_API_KEY"} ]

def getArguments():
    return [{"name": "anthropic_api_key", "description": "Anthropic api key", "default":None}]



class Client:
    def __init__(self,config):
        self.config = config
        anthropic_key = config.anthropic_api_key
        if not anthropic_key:
            log.error(f'API key not found. Please set the TULP_ANTHROPIC_API_KEY environment variable or add it to {config.CONFIG_FILE()}')
            log.error(f"If you don't have one, please create one at: https://console.anthropic.com")
            sys.exit(1)
        self.client = anthropic.Anthropic(api_key=anthropic_key)
        

    def convertMessagesFromOpenAI(self, messages):
        # from anthropic API:
        #ach input message must be an object with a role and content. You can specify a single user-role message, or you can include multiple user and assistant messages. The first message must always use the user role.

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
        """
        Writes the given content to the given file name. If the file already exists, it will rename it to a new file on the same folder, appending to the file name a counter (like -1) and keeping the same extension. It will continually increase the counter until it finds a free object.

        :param file_name: The name of the file to write to.
        """

        pmsgs = self.convertMessagesFromOpenAI(messages)
        for req in pmsgs:
            log.debug(f"REQ: {req}")
        log.debug(f"Sending the request to llm...")
        response = self.client.messages.create(
                model=self.config.model,
                messages=pmsgs,
                max_tokens=1024)
        log.debug(f"ANS: {response}")
        #[DEBUG] ANS: Message(id='msg_01B9APcyvZAgWGabSWKJAfgF', content=[TextBlock(text='(#output)\nfind ~ -iname "*love*" -type f 2>/dev/null\n(#comment)\nThe created find command will search for files in your home directory and all its subdirectories with a case-insensitive name that contains "love". The "-type f" option restricts the results to regular files only, excluding directories and other special file types. Any error messages are discarded by redirecting the standard error to /dev/null.', type='text')], model='claude-3-opus-20240229', role='assistant', stop_reason='end_turn', stop_sequence=None, type='message', usage=Usage(input_tokens=776, output_tokens=103))

        return { 
                "role": response.role,
                "content": response.content[0].text,
                "finish_reason": response.stop_reason
               }
