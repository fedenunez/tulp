#!/usr/bin/python3
# main.py - Entry point script for running tulp

import sys
# Ensure the package directory is discoverable if running script directly
# This might not be needed if installed via pip, but good practice for local dev.
import os
package_dir = os.path.dirname(os.path.abspath(__file__))
# Add the parent directory of 'tulp' package to sys.path if 'tulp' is inside the project root
project_root = os.path.dirname(package_dir)
if package_dir not in sys.path:
     sys.path.insert(0, package_dir)
if project_root not in sys.path:
     sys.path.insert(0, project_root)


from tulp import cli

if __name__ == "__main__":
    cli.run()

