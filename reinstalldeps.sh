#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# upgrade pip
pip install --upgrade pip
# upgrade setuptools
pip install --upgrade setuptools

# Get a list of all installed packages
pip freeze > installed.txt

# Uninstall all installed packages
pip uninstall -y -r installed.txt

# Remove the file we used to list all installed packages
rm installed.txt

# Install packages from requirements.txt
pip install -r requirements.txt