import argparse

from ... import subtract

parser = argparse.ArgumentParser(description="Subtract two numbers. Compute ( x - y )")
parser.set_defaults(handler=lambda args: print(subtract(args.x, args.y)))
parser.add_argument("x", type=float)
parser.add_argument("y", type=float)
