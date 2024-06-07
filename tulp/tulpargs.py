import os
import argparse
import re
from . import llms

CONFIG_FILE=os.path.expanduser("~/.tulp.conf")

def model_type(arg_value):
   client = llms.getModelModule(arg_value)
   if (not client):
       raise argparse.ArgumentTypeError("Invalid model")
   return arg_value

class TulpArgs:
    _instance = None

    def loadLlmsArguments(self,parser):
        for o in llms.getArguments():
            parser.add_argument(f'--{o["name"]}', type=str, help=o['description'])

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            parser = argparse.ArgumentParser(description=f"""TULP Understands Language Promptly:
A command line tool, in the best essence of POSIX tooling, that will help you
to **process**, **filter**, and **create** data in this new Artificial
Intelligence world.

Tulp support different backends and models, the backend will be automatically selected for each model, currently supported models should match:
{llms.getModelsDescription()}

""",
formatter_class=argparse.RawTextHelpFormatter
)
            parser.add_argument('-x', action='store_true', help='Allow tulp to create a program and execute it to fulfill the task (code interpret)')

            parser.add_argument('-w', type=str, help='Write the output (or the created program for execution) to the file. If the file exists, a backup will be created before overwriting it.')


            parser.add_argument('--model', type=model_type, help='Select the openai LLM model to use (default: gpt-4-turbo)')

            parser.add_argument('--max-chars', type=int, help='Number of chars per message chunk per request (Default 40000)')
            parser.add_argument('--cont', type=int, help='Autmatically ask the model to continue until it finishes the answering the request up to the given times')

            parser.add_argument('-v', action='store_true', help='Be verbose!')

            parser.add_argument('-q', action='store_true', help='Be quiet! Only print the answer and errors.')

            cls._instance.loadLlmsArguments(parser)

            parser.add_argument('request', nargs=argparse.REMAINDER, help="User request, instructions written in natural language")




            args = parser.parse_args()
            cls._instance.args = args

            if 'help' in args:
                parser.print_help()
                return

            if 'request' in args:
                args.request = " ".join(args.request)


        return cls._instance

    def get(self):
        return self.args
