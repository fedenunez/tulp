
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from .. import tulplogger
log = tulplogger.Logger()

def getModels():
   return [ { "idRe":"gemini.*", "description":  "Any Google gemini model (https://ai.google.dev/gemini-api/docs/models/gemini), requires gemini_api_key definition"} ]

def getArguments():
    return [{"name": "gemini_api_key", "description": "gemini cloud API KEY", "default":None}]


class Client:
    def __init__(self,config):
        self.config = config
        key = config.gemini_api_key
        if not key:
            log.error(f'Gemini API key not found. Please set the TULP_GEMINI_API_KEY environment variable or add it to {tulpconfig.CONFIG_FILE}')
            sys.exit(1)
        genai.configure(api_key=key)

        # Safety config
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
                },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
                },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
                },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
                },
            ]




    def convertMessagesFromOpenAIToGemini(self, messages):
        gmessages = []
        pRole = None
        pParts = None
        for msg in messages:
            mRole = msg['role']
            if mRole == "assistant" or mRole == "model":
              cRole = "model"
            elif mRole == "system" and (pRole == "system" or pRole==None): 
              # system is only accepted as the first system_instruction, any other message will be converted to user
              cRole = "system"
            else:
              cRole = "user"
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
           # 
           if pRole == "model": # as gemini does not allow the last message to be from model, we change it to be user, a needed hack to survive
               pRole = "user"
               if gmessages[-1]['role'] == pRole:
                   gmessages[-1]['parts'].extend(pParts)
               else: 
                   gmessages.append( {'role': pRole , 'parts': pParts } )
           else:
               gmessages.append( {'role': pRole , 'parts': pParts } )

        return gmessages




    def generate(self, messages):
        """
        Writes the given content to the given file name. If the file already exists, it will rename it to a new file on the same folder, appending to the file name a counter (like -1) and keeping the same extension. It will continually increase the counter until it finds a free object.

        :param file_name: The name of the file to write to.
        """

        gmessages = self.convertMessagesFromOpenAIToGemini(messages)
        if gmessages[0]['role'] == "system":
            self.model = genai.GenerativeModel(self.config.model, system_instruction="\n".join(gmessages[0]['parts']))
            log.debug(f"Adding system message!")
            gmessages = gmessages[1:]
        else:
            self.model = genai.GenerativeModel(self.config.model)


        for req in gmessages:
            log.debug(f"REQ: {req}")

        log.debug("Sending the request to llm...")

        generation_config = {
                "candidate_count": 1,
                "temperature": 1
                }

        response = self.model.generate_content(
                gmessages,
                safety_settings=self.safety_settings,
                request_options={"timeout": 900},
                generation_config=generation_config
                )

        while response.candidates[0].finish_reason.name == "RECITATION" and generation_config["temperature"] <=2 :
            generation_config["temperature"] += .33
            log.info(f"RECITATION detected, retrying with higher temperature: {generation_config['temperature']}..")

            response = self.model.generate_content(
                    gmessages,
                    safety_settings=self.safety_settings,
                    request_options={"timeout": 900},
                    generation_config=generation_config
                    )

        if response.candidates[0].finish_reason.name == "RECITATION":
            log.error(f"Okay, giving up. RECITATION is still popping up after retrying.")

        cand = response.candidates[0]
        log.debug(f"ANS: {cand}")
        log.debug(f"ANS: finish: {cand.finish_reason}")

        # https://ai.google.dev/api/rest/v1/GenerateContentResponse#FinishReason
        return { 
                "role": cand.content.role,
                "content": cand.content.parts[0].text,
                "finish_reason": cand.finish_reason
                }
