#!/usr/bin/python3
import sys


def run():
    print("""
tulip was renamed to tulp
=========================

Tulip package is now tulp, you can `pip uninstall pytulip` and `pip install tulp` package to be sure that you are up to date.

Anyway, tulp is already installed on your setup so you can go ahead and use it: `tulp [your prompt]`.

""")
    sys.exit(1)

if __name__ == "__main__":
    run()
