import argparse
import pkgutil
import sys
from collections import OrderedDict
from importlib import import_module
from itertools import groupby
from types import ModuleType
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple


__version__ = "0.0.4"


CommandName = str
CommandParts = Tuple[str, ...]
ParentCommandParts = Tuple[str, ...]


def create_parser(command_pkg: ModuleType) -> argparse.ArgumentParser:
    parsers = load_parsers(command_pkg)
    parsers = insert_missing_index_parsers(parsers)
    grouped_parsers = groupby_subcommand(parsers)
    subparsers_actions = get_subparsers_actions(grouped_parsers)
    root_parser = link_parsers(grouped_parsers, subparsers_actions)
    return root_parser


def load_parsers(
    command_pkg: ModuleType,
) -> "OrderedDict[CommandParts, argparse.ArgumentParser]":
    pkg_path = command_pkg.__path__  # type: ignore
    pkg_name = command_pkg.__name__
    parsers: List[Tuple[CommandParts, argparse.ArgumentParser]] = []

    for _, name, ispkg in pkgutil.walk_packages(pkg_path, prefix=pkg_name + "."):
        if ispkg:
            continue  # we only care about modules
        mod = import_module(name, pkg_name)
        parser = getattr(mod, "parser", None)
        if parser is None:
            continue  # there's no parser in this module
        parts = tuple(name.split("."))
        # TODO: 'commands' is hard-coded here, infer from pkg_name??
        parsers.append((parts[parts.index("commands") + 1 :], parser))  # noqa: E203

    return OrderedDict(sorted(parsers, key=lambda item: (-len(item[0]), item[0])))


def insert_missing_index_parsers(
    parsers: "OrderedDict[CommandParts, argparse.ArgumentParser]",
) -> "OrderedDict[CommandParts, argparse.ArgumentParser]":
    _parsers: Dict[CommandParts, argparse.ArgumentParser] = {}

    # insert index parsers for existing subcommands
    for parts, parser in list(parsers.items()):
        # add this parser to the new dict of parsers
        _parsers[parts] = parser
        if len(parts) and parts[-1] != "_index":
            # insert an index parser for this subcommand if one doesn't exist
            index_parts = _get_index_parts(parts)
            _parsers.setdefault(index_parts, argparse.ArgumentParser())

    # insert intermediate index parsers
    index_parser_keys = [k for k in _parsers.keys() if len(k) and k[-1] == "_index"]
    for index_parts in index_parser_keys:
        for i in range(len(index_parts)):
            parts = index_parts[: len(index_parts) - 1 - i] + index_parts[-1:]
            _parsers.setdefault(parts, argparse.ArgumentParser())

    return OrderedDict(
        sorted(_parsers.items(), key=lambda item: (-len(item[0]), item[0]))
    )


def _get_index_parts(parts: Tuple[str, ...]) -> Tuple[str, ...]:
    return (*parts[:-1], "_index")


def groupby_subcommand(
    parsers: "OrderedDict[CommandParts, argparse.ArgumentParser]",
) -> "OrderedDict[ParentCommandParts, OrderedDict[CommandName, argparse.ArgumentParser]]":  # noqa: E501
    groups = groupby(parsers.items(), key=lambda item: item[0][:-1])
    return OrderedDict(
        (k, OrderedDict((parts[-1], parser) for parts, parser in g)) for k, g in groups
    )


def get_subparsers_actions(
    grouped_parsers: "OrderedDict[ParentCommandParts, OrderedDict[CommandName, argparse.ArgumentParser]]",  # noqa: E501
) -> Dict[CommandParts, argparse._SubParsersAction]:
    subparsers_actions: Dict[CommandParts, argparse._SubParsersAction] = {}
    for subcommand, parsers in grouped_parsers.items():
        for name, parser in parsers.items():
            is_intermediate = _is_intermediate_index_parser(
                (*subcommand, name), grouped_parsers
            )
            if name == "_index" and (len(parsers) > 1 or is_intermediate):
                # only call .add_subparsers() if there's actually a need
                subparsers_actions[(*subcommand, name)] = parser.add_subparsers(
                    description=" "
                )
    return subparsers_actions


def link_parsers(
    grouped_parsers: "OrderedDict[ParentCommandParts, OrderedDict[CommandName, argparse.ArgumentParser]]",  # noqa: E501
    subparsers_actions: Dict[CommandParts, argparse._SubParsersAction],
) -> argparse.ArgumentParser:
    for subcommand, parsers in grouped_parsers.items():
        # link the terminal parsers at this level to the index parser at this level.
        for name, parser in parsers.items():
            # link each non-index parser to the index parser
            if name == "_index":
                continue
            prog = " ".join((sys.argv[0].split("/")[-1], *subcommand, name))
            parser_config = _extract_parser_config(parser)
            parser_config.update(dict(prog=prog, add_help=False))
            index_parts = (*subcommand, "_index")
            sp = subparsers_actions[index_parts]
            sp.add_parser(name, parents=[parser], **parser_config)

        # link the index parser for this command to the index parser of the
        # parent command
        # NOTE: this linking has to be done _after_ all the child parsers have been
        #       connected otherwise the children won't show up under the index.
        if not len(subcommand):
            continue
        sp = subparsers_actions[(*subcommand[:-1], "_index")]
        sp.add_parser(
            subcommand[-1],
            parents=[parsers["_index"]],
            description=parsers["_index"].description,
            add_help=False,
        )

    root_parser = grouped_parsers[tuple()]["_index"]
    return root_parser


def _extract_parser_config(parser: argparse.ArgumentParser) -> Dict[str, Any]:
    return {k: v for k, v in vars(parser).items() if not k.startswith("_")}


def _is_intermediate_index_parser(
    index_parts: CommandParts,
    grouped_parsers: "OrderedDict[ParentCommandParts, OrderedDict[CommandName, argparse.ArgumentParser]]",  # noqa: E501
):
    return (
        len(
            [
                k
                for k in grouped_parsers.keys()
                if len(k) == len(index_parts) and k[-1] != "_index"
            ]
        )
        > 0
    )
