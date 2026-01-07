import argparse

from ... import negate

parser = argparse.ArgumentParser(description="Negate a number. Compute ( -x )")
parser.set_defaults(handler=lambda args: print(negate(args.x)))
parser.add_argument("x", type=float)
