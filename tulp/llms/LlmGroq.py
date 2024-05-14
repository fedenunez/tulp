from groq import Groq
from .. import tulplogger
log = tulplogger.Logger()



def getModels():
   return [ { "idRe":"groq.*", "description":  "Any groq model id using the prefix 'groq.', will use GROQCLOUD API and requires GROQ_API_KEY definition. Check available modules at https://console.groq.com/docs/models" }]

def getArguments():
    return [{"name": "groq_api_key", "description": "GROQ cloud API KEY", "default":None}]


class Client:
    def __init__(self,config):
        self.config = config
        key = config.groq_api_key
        self.client = Groq(api_key=key)

    def getModel(self):
        return self.config.model[5:] if self.config.model.startswith("groq.") else self.config.model



    def convertMessagesFromOpenAI(self, messages):
        return messages




    def generate(self, messages):
        """
        Writes the given content to the given file name. If the file already exists, it will rename it to a new file on the same folder, appending to the file name a counter (like -1) and keeping the same extension. It will continually increase the counter until it finds a free object.

        :param file_name: The name of the file to write to.
        """
        gmessages = self.convertMessagesFromOpenAI(messages)
        for req in gmessages:
            log.debug(f"REQ: {req}")
        log.debug(f"Sending the request to llm...")
        response = self.client.chat.completions.create( messages=gmessages ,
                # The language model which will generate the completion.
                model=self.getModel(),

                #
                # Optional parameters
                #

                # Controls randomness: lowering results in less random completions.
                # As the temperature approaches zero, the model will become deterministic
                # and repetitive.
                temperature=0.5,

                # The maximum number of tokens to generate. Requests can use up to
                # 32,768 tokens shared between prompt and completion.
                max_tokens=1024,

                # Controls diversity via nucleus sampling: 0.5 means half of all
                # likelihood-weighted options are considered.
                top_p=1,

                # A stop sequence is a predefined or user-specified text string that
                # signals an AI to stop generating content, ensuring its responses
                # remain focused and concise. Examples include punctuation marks and
                # markers like "[end]".
                stop=None,

                # If set, partial message deltas will be sent.
                stream=False,
                )

        # chat_completion.choices[0].message.content
#        [DEBUG] ANS: Choice(finish_reason='stop', index=0, logprobs=None, message=ChoiceMessage(content='(#output)\n```bash\nfind / -name "lovely\\*file" 2>/dev/null\n```\n(#comment)\nThe above command will search for files and directories named "lovely*file" starting from the root directory ("/"). The "2>/dev/null" part is used to redirect error messages (such as permission errors) to null, effectively hiding them from the output.\n\n(#error)\n(#comment)', role='assistant', tool_calls=None))

        cand = response.choices[0]
        log.debug(f"ANS: {cand}")
        return { 
                "role": cand.message.role,
                "content": cand.message.content,
                "finish_reason": cand.finish_reason
               }
