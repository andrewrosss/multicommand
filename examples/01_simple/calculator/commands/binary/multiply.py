import argparse

from ... import multiply

parser = argparse.ArgumentParser(description="Multiply two numbers. Compute ( x * y )")
parser.set_defaults(handler=lambda args: print(multiply(args.x, args.y)))
parser.add_argument("x", type=float)
parser.add_argument("y", type=float)
