"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

import pathlib

from setuptools import find_packages
from setuptools import setup

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")


setup(
    name="calculator",
    version="1.0.0",
    description="A simple calculator in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/andrewrosss/multicommand/tree/master/examples/01_simple",
    author="Andrew Ross",
    author_email="andrew.ross.mail@gmail.com",
    packages=find_packages(),
    python_requires=">=3.10, <4",
    install_requires=["multicommand"],
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    # For example, the following would provide a command called `mycalc` which
    # executes the function `main` from the cli module in the calculator package
    # when invoked:
    entry_points={
        "console_scripts": [
            "mycalc=calculator.cli:main",
        ],
    },
)
