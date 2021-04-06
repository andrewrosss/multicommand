# multicommand

Simple subcommand CLIs with argparse.

[![PyPI Version](https://img.shields.io/pypi/v/multicommand.svg)](https://pypi.org/project/multicommand/)

`multicommand` uses only the standard library and is ~100 lines of code (modulo comments and whitespace)

## Installation

```bash
pip install multicommand
```

## Overview

Multicommand enables you to easily write CLIs with deeply nested commands using vanilla argparse. You provide it with a package, it searches that package for parsers (`ArgumentParser` objects), and connects, names, and converts those parsers into subcommands based on the package structure.

```text
        Package                       ->                    CLI


commands/unary/negate.py                            mycli unary negate ...
commands/binary/add.py                              mycli binary add ...
commands/binary/divide.py             ->            mycli binary divide ...
commands/binary/multiply.py                         mycli binary multiply ...
commands/binary/subtract.py                         mycli binary subtract ...
```

All it needs is for each module to define a module-level `parser` variable which points to an instance of `argparse.ArgumentParser`.

## Motivation

I like `argparse`. It's flexible, full-featured and it's part of the standard library, so if you have python you probably have argparse. I also like the "subcommand" pattern, i.e. one root command that acts as an entrypoint and subcommands to group related functionality. Of course, argparse can handle adding subcommands to parsers, but it's always felt a bit cumbersome, especially when there are many subcommands with lots of nesting.

If you've ever worked with technologies like `Next.js` or `oclif` (or even if you haven't) there's a duality between files and "objects". For Next.js each file under `pages/` maps to a webpage, in oclif each module under `commands/` maps to a CLI command. And that's the basic premise for multicommand: A light-weight package that let's you write one parser per file, pretty much in isolation, and it handles the wiring, exploiting the duality between command structure and file system structure.

## Getting Started

See the [simple example](https://github.com/andrewrosss/multicommand/tree/master/examples/01_simple), or for the impatient:

Create a directory to work in, for example:

```bash
mkdir ~/multicommand-sample && cd ~/multicommand-sample
```

Install `multicommand`:

```bash
python3 -m venv ./venv
source ./venv/bin/activate

python3 -m pip install multicommand
```

Create the subpackage to house our parsers:

```bash
mkdir -p mypkg/parsers/topic/cmd/subcmd
```

Create the `*.py` files required for the directories to be packages

```bash
touch mypkg/__init__.py
touch mypkg/parsers/__init__.py
touch mypkg/parsers/topic/__init__.py
touch mypkg/parsers/topic/cmd/__init__.py
touch mypkg/parsers/topic/cmd/subcmd/{__init__.py,greet.py}
```

Add a `parser` to `greet.py`:

```python
# file: mypkg/parsers/topic/cmd/subcmd/greet.py
import argparse


def handler(args):
    greeting = f'Hello, {args.name}!'
    print(greeting.upper() if args.shout else greeting)


parser = argparse.ArgumentParser(
    description='My first CLI with multicommand',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument('name', help='Name to use in greeting')
parser.add_argument('--shout', action='store_true', help='Yell the greeting')
parser.set_defaults(handler=handler)
```

lastly, add an entrypoint:

```bash
touch mypkg/cli.py
```

with the following content:

```python
# file: mypkg/cli.py
import multicommand
from . import parsers


def main():
    parser = multicommand.create_parser(parsers)
    args = parser.parse_args()
    if hasattr(args, 'handler'):
        args.handler(args)
        return
    parser.print_help()


if __name__ == "__main__":
    exit(main())
```

Try it out!

```bash
$ python3 -m mypkg.cli
usage: cli.py [-h] {topic} ...

optional arguments:
  -h, --help  show this help message and exit

subcommands:

  {topic}
```

Take a look at our `greet` command:

```bash
$ python3 -m mypkg.cli topic cmd subcmd greet --help
usage: cli.py topic cmd subcmd greet [-h] [--shout] name

My first CLI with multicommand

positional arguments:
  name        Name to use in greeting

optional arguments:
  -h, --help  show this help message and exit
  --shout     Yell the greeting (default: False)
```

From this we get:

```bash
$ python3 -m mypkg.cli topic cmd subcmd greet "World"
Hello, World!

$ python3 -m mypkg.cli topic cmd subcmd greet --shout "World"
HELLO, WORLD!
```

### Bonus

Want to add the command `topic cmd ungreet ...` to say goodbye?

Add the module:

```bash
touch mypkg/parsers/topic/cmd/ungreet.py
```

with contents:

```python
# file: mypkg/parsers/topic/cmd/ungreet.py
import argparse


def handler(args):
    print(f'Goodbye, {args.name}!')


parser = argparse.ArgumentParser(description='Another subcommand with multicommand')
parser.add_argument('name', help='Name to use in un-greeting')
parser.set_defaults(handler=handler)
```

The new command is automatically added!:

```bash
$ python3 -m mypkg.cli topic cmd --help
usage: cli.py cmd [-h] {subcmd,ungreet} ...

optional arguments:
  -h, --help        show this help message and exit

subcommands:

  {subcmd,ungreet}
```

Try it out:

```bash
$ python3 -m mypkg.cli topic cmd ungreet "World"
Goodbye, World!
```
