
import google.generativeai as genai
from .. import tulplogger
log = tulplogger.Logger()


class LlmGemini:
    def __init__(self,config):
        self.config = config
        key = config.gemini_api_key
        if not key:
            log.error(f'Gemini API key not found. Please set the TULP_GEMINI_API_KEY environment variable or add it to {tulpconfig.CONFIG_FILE}')
            sys.exit(1)
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel('gemini-pro')

    def convertMessagesFromOpenAIToGemini(self, messages):
        gmessages = []
        pRole = None
        pParts = None
        for msg in messages:
            cRole = "user"#(msg['role'] == "model" and "model" or "user")
            if pRole and cRole != pRole:
               gmessages.append( {'role': pRole , 'parts': pParts } )
               pRole = None
            if not pRole:
                pRole = cRole
                pParts = [msg['content']]
            else:
                pParts.append(msg['content'])
        # append the pending messages
        if pRole:
               gmessages.append( {'role': pRole , 'parts': pParts } )

        return gmessages




    def generate(self, messages):
        """
        Writes the given content to the given file name. If the file already exists, it will rename it to a new file on the same folder, appending to the file name a counter (like -1) and keeping the same extension. It will continually increase the counter until it finds a free object.

        :param file_name: The name of the file to write to.
        """
        gmessages = self.convertMessagesFromOpenAIToGemini(messages)
        for req in gmessages:
            log.debug(f"REQ: {req}")
        log.debug(f"Sending the request to llm...")
        #response = self.model.generate_content(messages)
        model = genai.GenerativeModel('gemini-pro')

        response = self.model.generate_content(gmessages)
        cand = response.candidates[0]
        log.debug(f"ANS: {cand.content}")
        log.debug(f"ANS: finish: {cand.finish_reason}")
        return { 
                "response_text": cand.content.parts[0].text,
                "finish_reason": cand.finish_reason
               }
