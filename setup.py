from setuptools import setup, find_packages

setup(
    name='tulp',
    version='0.3.2',
    py_modules=("tulp","tulplogger", "tulpconfig", "requestPrompt", "filteringPrompt"),
    install_requires=[
        'openai',
    ],
    author='Federico Nuñez (fedenunez)',
    author_email='fedenunez@gmail.com',
    maintainer='Federico Nuñez (fedenunez)',
    maintainer_email='fedenunez@gmail.com',
    description="""TULP: TULP Understands Language Perfectly

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
