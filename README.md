# multicommand

Simple subcommand CLIs with argparse.

## Installation

```bash
pip install multicommand
```

## Overview

`multicommand` enables you to easily write CLIs with deeply nested (sub)commands using argparse. Just created the directory structure that reflects the CLI command structure you want, write your parsers in "isolation" and multi command will do the rest.

multicommand turns a directory structure like this:

```text
commands/unary/negate.py
commands/binary/add.py
commands/binary/divide.py
commands/binary/multiply.py
commands/binary/subtract.py
```

Turns into a command line application like this:

```bash
mycli unary negate ...
mycli binary add ...
mycli binary divide ...
mycli binary multiply ...
mycli binary subtract ...
```

## Getting Started

See the [simple example](examples/01_simple/README.md).
