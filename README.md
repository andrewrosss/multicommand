# multicommand

Simple subcommand CLIs with argparse.

[![PyPI Version](https://img.shields.io/pypi/v/multicommand.svg)](https://pypi.org/project/multicommand/)

## Installation

```bash
pip install multicommand
```

## Overview

`multicommand` enables you to **easily** write CLIs with deeply nested commands using vanilla argparse.

Just create a directory structure that reflects the command structure you want, add a parser to each module (don't worry about hooking them up!), and multicommand will do the rest.

multicommand turns a directory structure like this:

```text
commands/unary/negate.py
commands/binary/add.py
commands/binary/divide.py
commands/binary/multiply.py
commands/binary/subtract.py
```

Into a command line application like this:

```bash
mycli unary negate ...
mycli binary add ...
mycli binary divide ...
mycli binary multiply ...
mycli binary subtract ...
```

All multicommand needs is for each module to define a module-level `parser` variable which points to an instance of `argparse.ArgumentParser`.

## Getting Started

See the [simple example](https://github.com/andrewrosss/multicommand/tree/master/examples/01_simple).
