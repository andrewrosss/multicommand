# Concepts

Contrary to what the [Basic Usage](./basic-usage) example might have you believing, `multicommand` doesn't quite treat all modules in the subpackage passed to `multicommand.create_parser(subpkg)` eqaully. In Fact, there are a few things to keep in mind in order to make using `multicommand` as smooth as possible.

Throughout the remainder of this discussion assume we're working in a package called `mypkg`, with an entrypoint (module + function) called `cli.py` and a subpackage called `commands` to house our parsers.

```text
mypkg
├── __init__.py
├── cli.py
└── commands
    ├── __init__.py
    └── ...
```

I.e. somewhere we're calling `multicommand.create_parser(mypkg.commands)`.

## The module-level `parser`

### The variable name

Each module in `commands/` - at least, the ones you want multicommand to find - must export (which, in python, really just means "must define") a module-level `parser` variable. Specifically, for every module in `commands/` that you want multicommand to use in the construction of the main root parser, must have a line something like:

```python title=mypkg/commands/some/module.py
import argparse

# other code

parser = argparse.ArgumentParser()
```

So the following "exports" would be ignored by multicommand

```python
# variable name is wrong
my_parser = argparse.ArgumentParser()
_parser = argparse.ArgumentParser()
command = argparse.ArgumentParser()

# this code is never executed when the module
# is imported, so multicommand doesn't see it
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

# similarly, defining a factory function and calling it later,
# multicommand doesn't see this either
def my_parser_factory() -> argparse.ArgumentParser:
    ...

my_parser_factory()
```

### The variable value

In addition to requiring a module-level `parser` variable, this variable must point at an instance of `argparse.ArgumentParser` (or an instance of a subclass of `argparse.ArgumentParser`).

That is, in addition so having `parser = ...` somewhere in the module, it should point at an appropriate instance.

So the following are **non-examples**:

```python
# `parser` points at the wrong instance types
parser = None
parser = 'fake-parser'

# Duck-typing a parser also won't work
class FakeParser:
    def add_argument(*args, **kwargs):
        ...

    def parser_args(argv: List[str]):
        ...

parser = FakeParser()
```

However, if the object pointed to by `parser` does inherit from `argparse.ArgumentParser`, it really doesn't matter how it came about, for example something like this **would** work:

```python title=mypkg/commands/some/module.py
import argparse


def my_parser_factory() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    # configure the parser ...

    return parser


parser = my_parser_factory()
```

This segues nicely to the next concept.

## A "parser module"

It's probably desirable to structure each module under `commands/` consistently. In general, having consistent coding habits is less of a statement toward multicommand usage and more so just a general programming best practice.

That said, if you have no opinions or are open to suggestions, a module structure something like the following might be useful to adopt:

```python title=mypkg/commands/some/module.py
import argparse

from mypkg import business_logic  # note the import from our local package


def create_parser() -> argparse.ArgumentParser:
    """A factory function to create the parser for handling this
    module's command. Its only job is creating, configuring, and
    returning the parser"""
    parser = argparse.ArgumentParser()

    # configure the parser ...

    # connect a handler function to this parser so that
    # this parser knows how to "handle itself"
    parser.set_defaults(handler=handler)

    return parser


def handler(args: argparse.Namespace) -> None:
    """A function that receives parsed args and sends them on to
    the "python API" exposed by this package. (I.e. the code that
    you'll probably have to import from somewhere else in this package"""
    param = args.param
    speacial_option = args.special_option

    business_logic.do_stuff(param, special_option)


# define the module-level parser so multicommand will find it 🚀
parser = create_parser()
```

The key take-aways from the above snippet are (in order of appearance):

- **Prefer absolute imports** - when importing objects from the local package absolute imports are _far_ easier to understand and digest than explicit relative imports, especially for deeply nested commands where you might have to go far "up the tree" and end up with something like `from ....subpkg.submodule import MyClass`.

  They're also more portable, and with the combination of `multicommand` and absolute imports, it means you can easily move/alter your command hierarchy just by moving files, whereas explicit relative imports would (likely) break after moving a module.

  [Further discussion](https://softwareengineering.stackexchange.com/a/159505)

- **Create a parser factory function (or class)** - This has two benefits.

  First, it nicely encapsulates the parser creation behind and easy-to-call function (or easy-to-instantiate class).

  Second, this encapsulation means it's easier to test your parsers. Need an instance of your parser? Call `create_parser`. Need another? Call `create_parser` again!

- **Embrace some kind of handler semantics** - As in the above example we define a handler function and link this function to the parser in the parser factory function. This has two benefits.

  First, the handlers become _the_ spots to look for where command line arguments are converted into python objects and subsequently passed to the packages python API.

  Second, by using some kind of consistent handler structure among modules we can simplify the entrypoint considerably. If we use the `handler`-style function defined above across all our parser modules, we can do something like this for the entrypoint:

  ```python title=mypkg/cli.py
  import multicommand

  import mypkg

  def main():
      parser = multicommand.create_parser(mypkg.commands)
      args = parser.parse_args()

      # call the handler if one exists
      if hasattr(args, 'handler'):
          return args.handler(args)

      # otherwise just print the usage
      parser.print_help()
  ```

## File Parsers

A **_file parser_** is any parser which comes from (is defined in):

- An importable _module_ (i.e. a file ending in `.py`)
- The module is located in the `commands/` (or similar) sub-package

These parsers basically map directly to some specific functionality of the CLI and "end there". That is, there are no further subcommands. If `git` was implemented with `multicommand` the parsers defining the `git add` and `git commit` commands could probably be _file parsers_.

In many (most?) cases file parsers are all you need, especially if the topology of the CLI is simple and/or only "one level deep", for example:

```bash
mycli add <thing>
mycli remove <thing>
mycli run <job_id> --option=<something>
mycli show
```

The above CLI might manifest itself with the following package structure:

```text
mypkg
├── __init__.py
├── cli.py
└── commands
    ├── __init__.py
    ├── add.py
    ├── remove.py
    ├── run.py
    └── show.py
```

## Directory Parsers

You may have noticed something in the [Bonus](basic-usage#bonus) section of the [Basic Usage](basic-usage) document. Specifically, take a look at the help produced by running `python -m mypkg.cli topic cmd --help` (reproduced here):

```bash
$ python3 -m mypkg.cli topic cmd --help
usage: cli.py topic cmd [-h] [command] ...

optional arguments:
  -h, --help  show this help message and exit

subcommands:

  [command]
    subcmd
    ungreet   Show an un-greeting
```

Notice the descriptions of the `subcommands`: `ungreet` has a description, but `subcmd` doesn't. Both `ungreet` and `subcmd` are valid substitutions for `[command]` (above). So how do we add a description for `subcmd` and how can we even target that command? It's represented as a **_directory_** (sub-package) after all!

As mentioned in the [Motivation](introduction#motivation) section of the [Introduction](introduction#motivation), `multicommand` aims to simplify authoring nested CLIs by _exploiting the duality between the filesystem hierarchy and command hierarchy._ In a filesystem there are files, but there are also directories! Well, basically everything's a file in linux filesystems, and there are more than two types of files, but for this analogy we only need to know that there are (at least) two types of objects in the tree.

I mention files and directories because in the same way that directories act as a parent node for files (and other nested directories) in a filesystem, _directory parsers_ act as the parent node for _file parsers_ (and other nested commands).

So, a **_directory parser_** is any parser which comes from (is defined in):

- A package's `__init__.py` file,
- The package is located in the `commands/` (or similar) sub-package.

These are the only requirements. Circling back to our [Basic Usage](basic-usage) question above, we could add a description by adding a _directory parser_ to the `__init__.py` of the `subcmd` package:

```python title=mypkg/parsers/topic/cmd/subcmd/__init__.py
import argparse


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Perform subcmd-like functions!')
    parser.set_defaults(handler=lambda args: None)
    return parser


parser = create_parser()
```

Adding this would yield:

```bash
$ python3 -m mypkg.cli topic cmd --help
usage: cli.py topic cmd [-h] [command] ...

optional arguments:
  -h, --help  show this help message and exit

subcommands:

  [command]
    subcmd    Perform subcmd-like functions!
    ungreet   Show an un-greeting
```

### Thoughts on directory parsers

**Directory parsers can act like file parsers.** A directory parser defined in `__init__.py` can have its own arguments and handler, effectively making it both a parent for subcommands _and_ a command in its own right. For example, `mycli topic` could accept arguments directly while also having `mycli topic subthing` as a subcommand.

**Directory parsers should generally only define options (flags), not positional arguments.** Since subcommand names are themselves positional, having a directory parser that expects positional arguments can create ambiguity or awkward UX. Stick to `--flag` style arguments for directory parsers.

**You often don't need to define directory parsers explicitly.** Throughout the examples so far, we haven't needed to create `__init__.py` files with parsers—multicommand automatically generates minimal directory parsers for any package in your command hierarchy. You only need to define one explicitly when you want to:

- Add a description (shown in parent's help text)
- Define shared options at that level
- Attach a handler for when the directory command is invoked without a subcommand
