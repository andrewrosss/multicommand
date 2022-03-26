from __future__ import annotations

import pkgutil
import sys
from argparse import _SubParsersAction  # type: ignore
from argparse import ArgumentParser
from dataclasses import dataclass
from dataclasses import field
from importlib import import_module
from types import ModuleType
from typing import Any
from typing import Iterator
from typing import NamedTuple
from typing import TypeVar
from typing import Union


__version__ = "1.0.0"
__all__ = ("create_parser",)

INDEX_MODULE = "_index"
PARSER_VARIABLE = "parser"
SHORT_SUMMARY_TRUNCATION_LENGTH = 50


def create_parser(
    command_pkg: ModuleType,
    prog: str | None = None,
    index_module: str = INDEX_MODULE,
    parser_variable: str = PARSER_VARIABLE,
) -> ArgumentParser:
    if prog is None:
        *_, prog = sys.argv[0].split("/")
    root = _create_index_node(command_pkg, prog, index_module, parser_variable)
    _populate_subparsers_actions(root)
    _link_parsers(root)
    return root.parser


@dataclass
class _TerminalNode:
    name: str
    parser: ArgumentParser


@dataclass
class _IndexNode:
    name: str
    parser: ArgumentParser = field(default_factory=lambda: ArgumentParser())
    subparsers_action: _SubParsersAction[ArgumentParser] | None = None
    children: list[_TerminalNode | _IndexNode] = field(
        init=False,
        repr=False,
        default_factory=list,
    )


_Node = Union[_IndexNode, _TerminalNode]
T = TypeVar("T")


# If multiple inheritance with NamedTuple was supported we could replace
# _TerminalInfo and _IndexInfo with a single generic _NodeInfo class
class _TerminalInfo(NamedTuple):
    node: _TerminalNode
    parents: tuple[_Node, ...] | None


class _IndexInfo(NamedTuple):
    node: _IndexNode
    parents: tuple[_Node, ...] | None


def _create_index_node(
    pkg: ModuleType,
    name: str,
    index_module: str,
    parser_variable: str,
) -> _IndexNode:
    index_node = _IndexNode(name)

    for info in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        *_, suffix = info.name.split(".")
        if not info.ispkg:
            # terminal parser
            mod = import_module(info.name)
            parser = getattr(mod, parser_variable, None)
            if not isinstance(parser, ArgumentParser):
                continue

            if suffix == index_module:
                index_node.parser = parser  # user has provided an index module
            else:
                node = _TerminalNode(suffix, parser)
                index_node.children.append(node)
        else:
            # index parser
            _pkg = import_module(info.name)
            node = _create_index_node(_pkg, suffix, index_module, parser_variable)
            index_node.children.append(node)

    return index_node


def _populate_subparsers_actions(node: _IndexNode):
    for n, _ in _iter_indexes(node):
        if len(n.children) == 0:
            continue  # this index parser has no children so it doesn't need subparsers
        p = n.parser
        n.subparsers_action = p.add_subparsers(description=" ", metavar="command")


def _link_parsers(node: _IndexNode) -> None:
    for index, parents in _iter_indexes(node):
        for child in index.children:
            if not index.subparsers_action:
                continue

            intermediate = [n.name for n in parents] if parents is not None else []
            prog = " ".join((*intermediate, index.name, child.name))
            parser_config = _extract_parser_config(child.parser)
            parser_config["prog"] = prog
            parser_config["help"] = _short_summary(child.parser.description)
            parser_config["add_help"] = False
            sp = index.subparsers_action
            sp.add_parser(child.name, parents=[child.parser], **parser_config)


def _iter_indexes(node: _IndexNode) -> Iterator[_IndexInfo]:
    for info in _iter_nodes_with_parents(node):
        if isinstance(info, _IndexInfo):
            yield info


def _iter_nodes_with_parents(
    node: _Node,
    parents: tuple[_Node, ...] | None = None,
) -> Iterator[_IndexInfo | _TerminalInfo]:
    """Traverse the tree depth-first post-order"""
    if isinstance(node, _IndexNode):
        _parents = (node,) if parents is None else parents + (node,)
        for child in node.children:
            yield from _iter_nodes_with_parents(child, _parents)
        yield _IndexInfo(node, parents)
    else:
        yield _TerminalInfo(node, parents)


def _short_summary(description: str | None) -> str | None:
    if description is None or len(description) <= SHORT_SUMMARY_TRUNCATION_LENGTH:
        return description
    return description[: SHORT_SUMMARY_TRUNCATION_LENGTH - 4] + " ..."


def _extract_parser_config(parser: ArgumentParser) -> dict[str, Any]:
    return {k: v for k, v in vars(parser).items() if not k.startswith("_")}
