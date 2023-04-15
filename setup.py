from setuptools import setup, find_packages


setup(
    name='pytulip',
    version='0.2.3',
    py_modules=["tulip"],
    install_requires=[ 'tulp' ],
    author='Federico Nuñez (fedenunez)',
    author_email='fedenunez@gmail.com',
    description="Tulip was renamed to tulp, from now one you should install and use tulp: `pip install tulp`",
    url='https://github.com/fedenunez/tulip',
    project_urls={ 'Source': 'https://github.com/fedenunez/tulip', },
    python_requires=">=3.7.1",
    entry_points='''
        [console_scripts]
        tulip=tulip:run
    ''',
    classifiers=["Development Status :: 7 - Inactive"],
)
