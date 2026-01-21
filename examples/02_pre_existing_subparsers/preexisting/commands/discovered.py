"""A command that multicommand should discover and add alongside the manual one."""

import argparse

parser = argparse.ArgumentParser(description="A discovered command")
parser.add_argument("name", help="A name to greet")


def handler(args):
    print(f"Hello, {args.name}!")


parser.set_defaults(handler=handler)
