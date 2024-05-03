import os
import sys
import importlib
import re

# Get the current directory path
current_dir = os.path.dirname(__file__)

# Create a list to store the submodules
submodules = []

# Iterate over all files in the directory
for file in os.listdir(current_dir):
    if file.endswith(".py") and file != "__init__.py":
        module_name = file[:-3]  # Remove the .py extension
        submodule = importlib.import_module(f"{__name__}.{module_name}")
        submodules.append(submodule)


arguments = None

def getArguments():
    global arguments
    if arguments == None:
        arguments = []
        for m in submodules:
            if hasattr(m, 'getArguments'):
                margs = m.getArguments()
                arguments.extend(margs)
    return arguments

models = None

def getModels():
    global models
    if models == None:
        models = []
        for m in submodules:
            if hasattr(m, 'getModels'):
                margs = m.getModels()
                for d in margs:
                    d["module"] = m
                models.extend(margs)
    return models


def getModelsDescription():
    models=getModels()
    description=""
    for m in models:
        description = description + f"\n   - {m['idRe']} : {m['description']}"
    return description

def getModelModule(modelname):
    models=getModels()
    for o in models:
       if re.compile(o["idRe"]).match(modelname):
           return o["module"]


def getModelClient(modelname, config):
    module = getModelModule(modelname)
    if module:
        return module.Client(config)
    raise Exception("Module not found!")
