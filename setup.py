"""
This simple `setup.py` tells `setuptools` to look at pyproject.toml` for configuration.
This is done because AWS SAM CLI (SAM CLI, version 1.120.0) does not seem to fully support 
configurations specified only in `pyproject.toml`. 
"""

from setuptools import setup

setup()