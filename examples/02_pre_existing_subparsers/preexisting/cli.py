import multicommand

from . import commands


def main():
    parser = multicommand.create_parser(commands)
    args = parser.parse_args()
    if hasattr(args, "handler"):
        args.handler(args)


if __name__ == "__main__":
    exit(main())
