# Basic Usage

We're going to create a small CLI with a single (deeply-nested) `greet` command/function:

```bash
<mycli> topic cmd subcmd greet ...
```

`<mycli>` is the placeholder for the name of the executable (in this case it's just going to end up being `python -m mypkg.cli`). `topic` is a command (we're already 1 level deep!). `cmd` is a subcommand of `topic`. `subcmd` is a subcommand of `cmd` (sub-subcommand of `topic`). Finally, `greet` is our actual function.

Normally we would need a fair bit of boilerplate to wire this up, but we'll see how `multicommand` makes this super easy.

## Setup

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

> **Note:** That's a long path. **Feel free to skip over this note and continue**, but if you're perplexed by this directory structure here's a high-level explanation:
>
> Part of that path should already be looking familiar. (The `topic/cmd/subcmd` part - that's no coicidence!) Basically, `mypkg` is the name of what will become our installable package (i.e. we'll eventually be able to `import mypkg`).
>
> The folder `mypkg/parsers` is going to be a sub-package (i.e it's going to contain an `__init__.py` file - in fact, all these folders will be sub-packages). This sub-package (`mypkg.parsers`) will be the thing that we pass to `multicommand`, from which we'll get our configured `argparse.ArgumentParser` instance.
>
> As for the remaining folders, `multicommand` will use those to create the command hierarchy that we're after.

Create the `*.py` files we'll need.

```bash
touch mypkg/__init__.py
touch mypkg/parsers/__init__.py
touch mypkg/parsers/topic/__init__.py
touch mypkg/parsers/topic/cmd/__init__.py
touch mypkg/parsers/topic/cmd/subcmd/{__init__.py,greet.py}
```

## The code

First, add a `parser` to `greet.py`:

```python title=mypkg/parsers/topic/cmd/subcmd/greet.py
import argparse


# using this handler we'll be able to tell this parser how to "handle itself"
def handler(args):
    greeting = f'Hello, {args.name}!'
    print(greeting.upper() if args.shout else greeting)


parser = argparse.ArgumentParser(
    description='Show a greeting',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument('name', help='Name to use in greeting')
parser.add_argument('--shout', action='store_true', help='Yell the greeting')
parser.set_defaults(handler=handler)  # link the handler to this parser/command
```

Second, add an entrypoint (this is the module we'll run from the command line):

```bash
touch mypkg/cli.py
```

with the following content:

```python title=mypkg/cli.py
import multicommand
from mypkg import parsers


def main():
    # pass the module 'mypkg.parsers' to multicommand for it to make us a parser
    parser = multicommand.create_parser(parsers)
    args = parser.parse_args()
    if hasattr(args, 'handler'):
        return args.handler(args)
    parser.print_help()


if __name__ == "__main__":
    exit(main())
```

Third, there is no third step! Let's try it out!

```bash
$ python3 -m mypkg.cli
usage: cli.py [-h] [command] ...

optional arguments:
  -h, --help  show this help message and exit

subcommands:

  [command]
    topic
```

Take a look at our `greet` command:

```bash
$ python3 -m mypkg.cli topic cmd subcmd greet --help
usage: cli.py topic cmd subcmd greet [-h] [--shout] name

Show a greeting

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

## Bonus

Want to add the command `<mycli> topic cmd ungreet ...` to say goodbye?

Add the module:

```bash
touch mypkg/parsers/topic/cmd/ungreet.py
```

> **Note:** Notice that since we want to create the command `<mycli> topic cmd ungreet ...` we're creating the module `<sub-pkg-that-we'll-pass-to-multicommand>/topic/cmd/ungreet.py`, where in this case `<sub-pkg-that-we'll-pass-to-multicommand>` is `mypkg/parsers/`

with contents:

```python title=mypkg/parsers/topic/cmd/ungreet.py
import argparse


def handler(args):
    print(f'Goodbye, {args.name}!')


parser = argparse.ArgumentParser(description='Show an un-greeting')
parser.add_argument('name', help='Name to use in un-greeting')
parser.set_defaults(handler=handler)
```

The new command is automatically added!:

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

Try it out:

```bash
$ python3 -m mypkg.cli topic cmd ungreet "World"
Goodbye, World!
```
