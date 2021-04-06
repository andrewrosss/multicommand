import pkgutil
import sys
from argparse import _SubParsersAction
from argparse import ArgumentParser
from collections import OrderedDict
from importlib import import_module
from itertools import groupby
from pathlib import PurePath
from types import ModuleType
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple


__version__ = "0.0.7"


def create_parser(command_pkg: ModuleType) -> ArgumentParser:
    parsers = load_parsers(command_pkg)
    registry = create_registry(parsers)
    root_parser = link_parsers(registry)
    return root_parser


def load_parsers(
    command_pkg: ModuleType,
) -> List[Tuple[PurePath, ArgumentParser]]:
    pkg_path = command_pkg.__path__  # type: ignore
    pkg_name = command_pkg.__name__
    pkg_prefix = f"{pkg_name}."
    parsers: List[Tuple[PurePath, ArgumentParser]] = []

    for _, name, ispkg in pkgutil.walk_packages(pkg_path, prefix=pkg_prefix):
        if ispkg:
            continue  # we only care about modules
        mod = import_module(name, pkg_name)
        parser = getattr(mod, "parser", None)
        if parser is None:
            continue  # there's no parser variable in this module
        parts = PurePath(*(name.replace(pkg_prefix, "").split(".")))
        parsers.append((parts, parser))

    return parsers


def create_registry(
    parsers: List[Tuple[PurePath, ArgumentParser]],
) -> "OrderedDict[PurePath, ArgumentParser]":
    _parsers = dict(parsers)
    # insert index parsers for existing subcommands if they don't already exist
    for path, _ in parsers:
        if len(path.parts) and path.name != "_index":
            index_path = path.parent / "_index"
            _parsers.setdefault(index_path, ArgumentParser())
    # insert intermediate index parsers if they don't already exist
    index_paths = [p for p in _parsers if p.name == "_index"]
    for index_path in index_paths:
        for intermediate_path in _iter_parents(index_path):
            _parsers.setdefault(intermediate_path / "_index", ArgumentParser())

    return OrderedDict(sorted(_parsers.items(), key=_sort_key))


def _iter_parents(fp: PurePath):
    while len(fp.parts):
        yield fp.parent
        fp = fp.parent


def _sort_key(item: Tuple[PurePath, ArgumentParser]):
    return (-len(item[0].parts), item[0])


def _groupby_subcommand(
    registry: "OrderedDict[PurePath, ArgumentParser]",
) -> List[Tuple[PurePath, List[Tuple[str, ArgumentParser]]]]:
    groups = groupby(registry.items(), key=lambda item: item[0].parent)
    return [(k, [(path.name, parser) for path, parser in g]) for k, g in groups]


def _create_subparsers_actions(
    registry: "OrderedDict[PurePath, ArgumentParser]",
) -> Dict[PurePath, _SubParsersAction]:
    grouped_parsers = _groupby_subcommand(registry)
    subparsers_actions: Dict[PurePath, _SubParsersAction] = {}
    for subcommand, parsers in grouped_parsers:
        for name, parser in parsers:
            path = subcommand / name
            is_intermediate = _is_intermediate_index_parser(path, grouped_parsers)
            if name == "_index" and (len(parsers) > 1 or is_intermediate):
                # only call .add_subparsers() if there's actually a need
                subparsers_actions[path] = parser.add_subparsers(description=" ")
    return subparsers_actions


def link_parsers(registry: "OrderedDict[PurePath, ArgumentParser]") -> ArgumentParser:
    grouped_parsers = _groupby_subcommand(registry)
    subparsers_actions = _create_subparsers_actions(registry)
    for subcommand, parsers in grouped_parsers:
        # link the terminal parsers at this level to the index parser at this level.
        for name, parser in parsers:
            if name == "_index":
                continue  # we're linking each non-index parser to the index parser
            prog = " ".join((sys.argv[0].split("/")[-1], *(subcommand.parts), name))
            parser_config = _extract_parser_config(parser)
            parser_config.update(dict(prog=prog, add_help=False))
            index_path = subcommand / "_index"
            sp = subparsers_actions[index_path]
            sp.add_parser(name, parents=[parser], **parser_config)

        # link the index parser for this command to the index parser of the
        # parent command
        # NOTE: this linking has to be done _after_ all the child parsers have been
        #       connected otherwise the children won't show up under the index.
        if not len(subcommand.parts):
            continue
        index_parser = [parser for name, parser in parsers if name == "_index"][0]
        sp = subparsers_actions[subcommand.parent / "_index"]
        sp.add_parser(
            subcommand.name,
            parents=[index_parser],
            description=index_parser.description,
            add_help=False,
        )

    root_parser = registry[PurePath("_index")]
    return root_parser


def _extract_parser_config(parser: ArgumentParser) -> Dict[str, Any]:
    return {k: v for k, v in vars(parser).items() if not k.startswith("_")}


def _is_intermediate_index_parser(
    index_path: PurePath,
    grouped_parsers: List[Tuple[PurePath, List[Tuple[str, ArgumentParser]]]],
):
    # TODO: this function only makes sense in the context where index_path has
    #       already been determined to not have any non-index sibling parsers,
    #       which _is_ the case when this function is called above, but
    #       outside that context it might not yeild the correct results.
    same_level_non_index_paths = [
        parent_path
        for parent_path, _ in grouped_parsers
        if len(parent_path.parts) == len(index_path.parts)
        and parent_path.name != "_index"
    ]
    return len(same_level_non_index_paths) > 0
