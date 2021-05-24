import pkgutil
import sys
from argparse import _SubParsersAction
from argparse import ArgumentParser
from collections import defaultdict
from collections import OrderedDict
from importlib import import_module
from pathlib import PurePath
from types import ModuleType
from typing import Any
from typing import DefaultDict
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union


__version__ = "0.1.0"
SHORT_SUMMARY_TRUNCATION_LENGTH = 50


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
        if not isinstance(parser, ArgumentParser):
            continue  # there was a parser, but it wasnt a (subclass of) ArgumentParser
        parts = PurePath(*(name.replace(pkg_prefix, "").split(".")))
        parsers.append((parts, parser))

    return parsers


def create_registry(
    parsers: List[Tuple[PurePath, ArgumentParser]],
) -> "OrderedDict[PurePath, Dict[str, ArgumentParser]]":
    # add the existing parsers
    _parsers: DefaultDict[PurePath, DefaultDict[str, ArgumentParser]]
    _parsers = defaultdict(lambda: defaultdict(ArgumentParser))
    for path, parser in parsers:
        _parsers[path.parent][path.name] = parser
    # insert index parsers for existing subcommands if they don't already exist
    for path, _ in parsers:
        if len(path.parts) and path.name != "_index":
            # asking for it creates a blank parser
            _parsers[path.parent]["_index"]
    _parsers[PurePath()]["_index"]  # init the root index parser if it does not exist
    # insert intermediate index parsers if they don't already exist
    index_paths = [s / n for s, p in _parsers.items() for n in p if n == "_index"]
    for index_path in index_paths:
        for intermediate_path in _iter_parents(index_path):
            # asking for it creates a blank parser
            _parsers[intermediate_path]["_index"]
    return OrderedDict({k: dict(v) for k, v in sorted(_parsers.items(), key=_sort_key)})


def _iter_parents(fp: PurePath):
    while len(fp.parts):
        yield fp.parent
        fp = fp.parent


def _sort_key(item: Tuple[PurePath, Dict[str, ArgumentParser]]):
    return (-len(item[0].parts), item[0])


def link_parsers(
    registry: "OrderedDict[PurePath, Dict[str, ArgumentParser]]",
) -> ArgumentParser:
    subparsers_actions = _create_subparsers_actions(registry)
    for subcommand, parsers in registry.items():
        # link the terminal parsers at this level to the index parser at this level.
        for name, parser in parsers.items():
            if name == "_index":
                continue  # we're linking each non-index parser to the index parser
            prog = " ".join((sys.argv[0].split("/")[-1], *(subcommand.parts), name))
            parser_config = _extract_parser_config(parser)
            parser_config.update(
                dict(prog=prog, add_help=False, help=_short_summary(parser.description))
            )
            index_path = subcommand / "_index"
            sp = subparsers_actions[index_path]
            sp.add_parser(name, parents=[parser], **parser_config)

        # link the index parser for this command to the index parser of the
        # parent command
        # NOTE: this linking has to be done _after_ all the child parsers have been
        #       connected otherwise the children won't show up under the index.
        if not len(subcommand.parts):
            continue
        index_parser = parsers["_index"]
        prog = " ".join((sys.argv[0].split("/")[-1], *(subcommand.parts)))
        parser_config = _extract_parser_config(index_parser)
        parser_config.update(
            dict(
                prog=prog, add_help=False, help=_short_summary(index_parser.description)
            )
        )
        sp = subparsers_actions[subcommand.parent / "_index"]
        sp.add_parser(subcommand.name, parents=[index_parser], **parser_config)

    root_parser = registry[PurePath()]["_index"]
    return root_parser


def _create_subparsers_actions(
    registry: "OrderedDict[PurePath, Dict[str, ArgumentParser]]",
) -> Dict[PurePath, _SubParsersAction]:
    subparsers_actions: Dict[PurePath, _SubParsersAction] = {}
    for subcommand, parsers in registry.items():
        for name, parser in parsers.items():
            path = subcommand / name
            if _requires_subparsers(registry, path):
                # only call .add_subparsers() if there's actually a need
                subparsers_actions[path] = parser.add_subparsers(
                    description=" ", metavar="[command]"
                )
    return subparsers_actions


def _requires_subparsers(
    registry: "OrderedDict[PurePath, Dict[str, ArgumentParser]]",
    path: PurePath,
):
    # non-index terminal parsers DO NOT get subparsers
    if path.name != "_index":
        return False
    # index parsers with sibling parsers DO get subparsers
    has_siblings = len(registry[path.parent]) > 1
    if has_siblings:
        return True
    # intermediate index parsers DO get subparsers
    same_level_non_index_paths = [
        other_path
        for other_path in registry
        if len(other_path.parts) == len(path.parts)  # same level/depth
        and other_path.parent.parts == path.parent.parts  # same parent
        and other_path.name != "_index"  # non-index parser
    ]
    is_intermediate = len(same_level_non_index_paths) > 0
    return is_intermediate


def _short_summary(description: Union[str, None]) -> Union[str, None]:
    if description is None or len(description) <= SHORT_SUMMARY_TRUNCATION_LENGTH:
        return description
    return description[: SHORT_SUMMARY_TRUNCATION_LENGTH - 4] + " ..."


def _extract_parser_config(parser: ArgumentParser) -> Dict[str, Any]:
    return {k: v for k, v in vars(parser).items() if not k.startswith("_")}
