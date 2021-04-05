# Simple Calculator CLI

## The Scenario

Suppose we've written a python package `calculator` which exposes some basic calculator functionality. It's a super simple package with the following structure:

```text
.
├── README.md
├── calculator
│   └── __init__.py
├── requirements.txt
└── setup.py
```

So simple in fact that all the action takes place in `calculator/__init__.py`, which contains the following code:

```python
def negate(x: float):
    return -x


def add(x: float, y: float):
    return x + y


def subtract(x: float, y: float):
    return x - y


def multiply(x: float, y: float):
    return x * y


def divide(x: float, y: float):
    return x / y

```

## Adding CLI skeleton

We have a nice little package that we've polished up and we'd like to make the functionality available from the command line.

After some thought, we'd like our CLI to look something like:

```bash
# we'll group the unary functions together under the 'unary' subcommand
mycalc unary negate <x>

# similarly we'll group the binary functiongs together under the 'binary' subcommand
mycalc binary add <x> <y>
mycalc binary subtract <x> <y>
mycalc binary multiply <x> <y>
mycalc binary divide <x> <y>
```

For the implementation we'll turn to `multicommand`. Multicommand needs us to create a subpackage, and in that subpackage we'll create a directory structure with files that mirror how we want our commands to look.

Specifically, inside our caclulator package we'll create a `commands/` folder. This will be the subpackage that will hold our commands.

Inside this new directory we'll create two directories: `unary/` and `binary/`. These correspond to the subcommands that our CLI will have: `mycalc unary` and `mycalc binary`.

Inside `unary/`, we'll create a module `negate.py`. The name of this file will become the name of our sub-subcommand: `mycalc unary negate`.

Inside `binary/`, we'll create the modules: `add.py`, `divide.py`, `multiply.py`, `subtract.py`. Again the module names will become subcommand names (as shown above).

All-in-all, we should have the following directory structure (the existing files have be omitted for brevity):

```text
.
└── calculator
    └── commands
        ├── binary
        │   ├── add.py
        │   ├── divide.py
        │   ├── multiply.py
        │   └── subtract.py
        └── unary
            └── negate.py
```

## Installing Dependencies

Before we go further we should install our dependencies. Activate a virtual env using whatever provider you like: virtualenv, pipenv, poetry, conda, etc. and install the dependencies:

```bash
pip install -r requirements.txt
```

## Creating the parsers

Now we need to write the parsers. The whole purpose of multicommand is so that we can write each command's `ArgumentParser` in "isolation", that is, we configure the parser in the appropriate module (located in `commands/`) and multicommand will handle wiring them all up.

Let's start with the `mycalc unary negate` command. Open up `commands/unary/negate.py` and add the following contents:

```python
# file: calculator/commands/unary/negate.py
import argparse

from ... import negate


# this module should define a parser variable that points to an
# instance of argparse.ArgumentParser so that multicommand will
# find and register the parser. You probably want every module
# in commands/ to do this.
parser = argparse.ArgumentParser(description="Negate a number. Compute ( -x )")

# to make our lives easier we're going to give every parser we
# define a handler, the handler should take an instance of
# argparse.Namespace and then ... well ... handle the arguments,
# so probably call/use one or more of our package's APIs
parser.set_defaults(handler=lambda args: negate(args.x))

# this parser is pretty basic and only needs to be able to parse
# a single argument
parser.add_argument("x", type=float)
```

OK, with this parser complete, we can do the rest. (Omitted here for brevity)

## Home stretch

Once we're done defining the parser there are 3 steps left:

1. Add `__init__.py`'s everywhere. (We need these so that the parsers are importable.)
1. Define an "entrypoint" function.
1. Update setup.py so that it knows about our entrypoint function.

Step 1. is easy, we should have created 3 empty `__init__.py` files:

```text
.
└── calculator
    └── commands
        ├── __init__.py  # here
        ├── binary
        │   ├── __init__.py  # here
        │   ├── add.py
        │   ├── divide.py
        │   ├── multiply.py
        │   └── subtract.py
        └── unary
            ├── __init__.py  # here
            └── negate.py
```

For Step 2. we'll make a module called `cli.py` inside of `calculator/`:

```text
.
└── calculator
    ├── cli.py  # here
    └── commands
        └── ...
```

Where the contents of cli.py is:

```python
import multicommand
from . import commands


def main():
    parser = multicommand.create_parser(commands)
    args = parser.parse_args()
    if hasattr(args, "handler"):
        args.handler(args)


if __name__ == "__main__":
    exit(main())
```

All we're doing here is importing `multicommand` and our `commands` subpackage, then we create a `main` function. This function uses `multicommand` to construct our root argument parser and checks if the parsed args (`argparse.Namespace` object) has a handler attribute, if it does, we run the handler.

At this point we can try out our CLI by running:

```bash
$ python -m calculator.cli --help
usage: cli.py [-h] {binary,unary} ...

optional arguments:
  -h, --help      show this help message and exit

subcommands:

  {binary,unary}
```

This looks promising!

But invoking the command this way (`python -m calculator.cli ...`) is pretty inconvenient, so what we can do is configure the `entry_points` parameter in `setup.py`:

```python
# file: setup.py

...

setup(
    ...
    entry_points={
        "console_scripts": [
            "mycalc=calculator.cli:main",
        ],
    },
)
```

Doing this means that when we install our `calculator` package (for example from pypi or locally using `pip install -e .`) we'll be able to invoke our CLI using the command `mycalc`.

For example, installing the package in editable mode:

```bash
pip install -e .
```

means that we'll be able to run the command `mycalc unary negate --help` and see the following:

```bash
$ mycalc unary negate --help
usage: mycalc unary negate [-h] x

Negate a number. Compute ( -x )

positional arguments:
  x

optional arguments:
  -h, --help  show this help message and exit
```

or

```bash
$ mycalc unary negate 281094801
-281094801.0
```

And that's all there is to it! A simple subcommand CLI where we didn't have to mess around with configuring subcommands and adding subparsers to parent parsers - we just wrote each command's argument parser in isolation and `multicommand` handled the rest.
