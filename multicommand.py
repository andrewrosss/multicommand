import argparse
import pkgutil
from collections import OrderedDict
from importlib import import_module
from itertools import groupby
from types import ModuleType
from typing import Dict
from typing import Tuple


__version__ = "0.0.2"


def create_parser(command_pkg: ModuleType) -> argparse.ArgumentParser:
    parsers = load_parsers(command_pkg)
    parsers = fill_index_parsers(parsers)
    grouped_parsers = groupby_subcommand(parsers)
    subparsers_actions = get_subparsers_actions(grouped_parsers)
    root_parser = link_parsers(grouped_parsers, subparsers_actions)
    return root_parser


def load_parsers(
    command_pkg: ModuleType,
) -> "OrderedDict[Tuple[str, ...], argparse.ArgumentParser]":
    pkg_path = command_pkg.__path__  # type: ignore
    pkg_name = command_pkg.__name__
    parsers = []

    for _, name, ispkg in pkgutil.walk_packages(pkg_path, prefix=pkg_name + "."):
        if ispkg:
            continue
        mod = import_module(name, pkg_name)
        parser = getattr(mod, "parser", None)
        if parser is None:
            continue
        rel_pkg_path = tuple(name.split("."))
        parsers.append(
            (rel_pkg_path[rel_pkg_path.index("commands") + 1 :], parser)  # noqa: E203
        )

    return OrderedDict(sorted(parsers, key=lambda item: (-len(item[0]), item[0])))


def fill_index_parsers(
    parsers: "OrderedDict[Tuple[str, ...], argparse.ArgumentParser]",
) -> "OrderedDict[Tuple[str, ...], argparse.ArgumentParser]":
    _parsers: Dict[Tuple[str, ...], argparse.ArgumentParser] = {}

    for parts, parser in list(parsers.items()):
        # add this parser to the new index of parsers
        _parsers[parts] = parser
        if len(parts) and parts[-1] != "_index":
            # try to create the index parser for this subcommand if it doesn't exist
            index_parts = _get_index_parts(parts)
            _parsers.setdefault(index_parts, argparse.ArgumentParser())

    return OrderedDict(
        sorted(_parsers.items(), key=lambda item: (-len(item[0]), item[0]))
    )


def _get_index_parts(parts: Tuple[str, ...]) -> Tuple[str, ...]:
    return parts[:-1] + ("_index",)


def groupby_subcommand(
    parsers: "OrderedDict[Tuple[str, ...], argparse.ArgumentParser]",
) -> "OrderedDict[Tuple[str, ...], OrderedDict[str, argparse.ArgumentParser]]":
    groups = groupby(parsers.items(), key=lambda item: item[0][:-1])
    return OrderedDict(
        (k, OrderedDict((parts[-1], parser) for parts, parser in g)) for k, g in groups
    )


def get_subparsers_actions(
    grouped_parsers: "OrderedDict[Tuple[str, ...], OrderedDict[str, argparse.ArgumentParser]]",  # noqa: E501
) -> Dict[Tuple[str, ...], argparse._SubParsersAction]:
    subparsers_actions: Dict[Tuple[str, ...], argparse._SubParsersAction] = {}
    for subcommand, parsers in grouped_parsers.items():
        for name, parser in parsers.items():
            if name == "_index" and len(parsers) > 1:
                # only call .add_subparsers() if there's actually a need
                subparsers_actions[subcommand + (name,)] = parser.add_subparsers(
                    description=" "
                )
    return subparsers_actions


def link_parsers(
    grouped_parsers: "OrderedDict[Tuple[str, ...], OrderedDict[str, argparse.ArgumentParser]]",  # noqa: E501
    subparsers_actions: Dict[Tuple[str, ...], argparse._SubParsersAction],
) -> argparse.ArgumentParser:
    for subcommand, parsers in grouped_parsers.items():
        for name, parser in parsers.items():
            # link each non-index parser to the index parser
            if name == "_index":
                continue
            index_parts = subcommand + ("_index",)
            sp = subparsers_actions[index_parts]
            sp.add_parser(
                name, parents=[parser], description=parser.description, add_help=False
            )

        # link the index parser for this group to the index parser 1 level up,
        # Note: this linking has to be done _after_ all the child parsers have
        # been connected otherwise the children won't show up under the index.
        if not len(subcommand):
            continue
        sp = subparsers_actions.get(subcommand[:-1] + ("_index",))
        sp.add_parser(
            subcommand[-1],
            parents=[parsers["_index"]],
            description=parsers["_index"].description,
            add_help=False,
        )

    root_parser = grouped_parsers[tuple()]["_index"]
    return root_parser
