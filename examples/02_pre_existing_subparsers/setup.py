"""A setuptools based setup module."""

import pathlib

from setuptools import find_packages
from setuptools import setup

here = pathlib.Path(__file__).parent.resolve()

setup(
    name="preexisting",
    version="1.0.0",
    description="Example CLI with pre-existing subparsers",
    url="https://github.com/andrewrosss/multicommand/tree/master/examples/02_pre_existing_subparsers",
    author="Andrew Ross",
    author_email="andrew.ross.mail@gmail.com",
    packages=find_packages(),
    python_requires=">=3.10, <4",
    install_requires=["multicommand"],
    entry_points={
        "console_scripts": [
            "preexisting=preexisting.cli:main",
        ],
    },
)
