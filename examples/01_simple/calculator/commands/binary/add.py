import argparse

from ... import add

parser = argparse.ArgumentParser(description="Add two numbers. Compute ( x + y )")
parser.set_defaults(handler=lambda args: print(add(args.x, args.y)))
parser.add_argument("x", type=float)
parser.add_argument("y", type=float)
