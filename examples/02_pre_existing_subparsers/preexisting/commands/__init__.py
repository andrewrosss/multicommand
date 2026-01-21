"""Commands package with pre-existing subparsers.

This demonstrates a parser that already has add_subparsers() called
before multicommand processes it. Multicommand should detect this
and reuse the existing subparsers action rather than failing.
"""

import argparse

# Create the top-level parser with pre-existing subparsers
# (This pattern is common when users want to define some subcommands
# manually while letting multicommand handle discovery of others)
parser = argparse.ArgumentParser(description="A CLI with pre-existing subparsers")
parser.add_argument(
    "--verbose", "-v", action="store_true", help="Enable verbose output"
)

# Pre-existing subparsers - multicommand must detect and reuse this
subparsers = parser.add_subparsers(help="available commands")

# A manually-defined subcommand
parser_manual = subparsers.add_parser("manual", help="A manually defined command")
parser_manual.add_argument("value", type=int, help="A value to process")


def manual_handler(args):
    if args.verbose:
        print(f"Verbose: Processing value {args.value}")
    print(f"Manual command result: {args.value * 2}")


parser_manual.set_defaults(handler=manual_handler)
