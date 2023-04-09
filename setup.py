from setuptools import setup, find_packages

setup(
    name='pytulp',
    version='0.2.2',
    py_modules=("tulp","tulplogger", "requestPrompt", "filteringPrompt"),
    install_requires=[
        'openai',
    ],
    author='Federico Nuñez (fedenunez)',
    author_email='fedenunez@gmail.com',
    description="""
TULP: TULP Understands Language Instructions Perfectly

A command line tool, in the best essence of POSIX tooling, that will help you to **process**, **filter**, and **create** data in this new Artificial Intelligence world.

""",
    url='https://github.com/fedenunez/tulp',
    project_urls={
        'Source': 'https://github.com/fedenunez/tulp',
    },
    python_requires=">=3.7.*",
    entry_points='''
        [console_scripts]
        tulp=tulp:run
    ''',
)
