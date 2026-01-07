import argparse

from ... import divide

parser = argparse.ArgumentParser(description="Divide two numbers. Compute ( x / y )")
parser.set_defaults(handler=lambda args: print(divide(args.x, args.y)))
parser.add_argument("x", type=float)
parser.add_argument("y", type=float)
