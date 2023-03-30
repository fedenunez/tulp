from setuptools import setup, find_packages

setup(
    name='pytulip',
    version='0.2.1',
    py_modules=("tulip","tuliplogger", "requestPrompt", "filteringPrompt"),
    install_requires=[
        'openai',
    ],
    author='You and me (fedenunez)',
    author_email='your_email@example.com',
    description="""
TULIP: TULIP Understands Language Instructions Perfectly

A command line tool, in the best essence of POSIX tooling, that will help you to **process**, **filter**, and **create** data in this new Artificial Intelligence world.

""",
    url='https://github.com/fedenunez/tulip',
    project_urls={
        'Source': 'https://github.com/fedenunez/tulip',
    },
    entry_points='''
        [console_scripts]
        tulip=tulip:run
    ''',
)
