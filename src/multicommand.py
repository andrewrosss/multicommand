from __future__ import annotations

import pkgutil
import sys
from argparse import ArgumentParser
from argparse import _SubParsersAction  # type: ignore
from dataclasses import dataclass
from dataclasses import field
from importlib import import_module
from types import ModuleType
from typing import Any
from typing import Iterator


__version__ = "1.0.0"
__all__ = ("create_parser",)

PARSER_VARIABLE = "parser"
SHORT_SUMMARY_TRUNCATION_LENGTH = 50


def create_parser(
    command_pkg: ModuleType,
    *,
    prog: str | None = None,
    parser_variable: str = PARSER_VARIABLE,
) -> ArgumentParser:
    if prog is None:
        *_, prog = sys.argv[0].split("/")
    root = _create_index_node(command_pkg, prog, parser_variable)
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
    parser: ArgumentParser
    subparsers_action: _SubParsersAction[ArgumentParser] | None = None
    children: list[_TerminalNode | _IndexNode] = field(
        init=False,
        repr=False,
        default_factory=list,
    )


_Node = _IndexNode | _TerminalNode


def _create_index_node(
    pkg: ModuleType,
    name: str,
    parser_variable: str,
) -> _IndexNode:
    index_parser = getattr(pkg, parser_variable, ArgumentParser())
    index_node = _IndexNode(name, index_parser)

    for info in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        *_, suffix = info.name.split(".")
        mod = import_module(info.name)

        if info.ispkg:
            # package (index parser)
            node = _create_index_node(mod, suffix, parser_variable)
            index_node.children.append(node)
        else:
            # module (terminal parser)
            term_parser = getattr(mod, parser_variable, None)
            if isinstance(term_parser, ArgumentParser):
                index_node.children.append(_TerminalNode(suffix, term_parser))

    return index_node


def _populate_subparsers_actions(node: _IndexNode):
    for n, _ in _iter_indexes(node):
        if n.children:
            n.subparsers_action = n.parser.add_subparsers(
                description=" ", metavar="command"
            )


def _link_parsers(node: _IndexNode) -> None:
    for index, parents in _iter_indexes(node):
        for child in index.children:
            if not index.subparsers_action:
                continue

            intermediate = [n.name for n in parents] if parents else []
            prog = " ".join((*intermediate, index.name, child.name))
            parser_config = _extract_parser_config(child.parser)
            parser_config["prog"] = prog
            parser_config["help"] = _short_summary(child.parser.description)
            parser_config["add_help"] = False
            index.subparsers_action.add_parser(
                child.name, parents=[child.parser], **parser_config
            )


def _iter_indexes(
    node: _IndexNode,
) -> Iterator[tuple[_IndexNode, tuple[_Node, ...] | None]]:
    for n, parents in _iter_nodes_with_parents(node):
        match n:
            case _IndexNode():
                yield n, parents


def _iter_nodes_with_parents(
    node: _Node,
    parents: tuple[_Node, ...] | None = None,
) -> Iterator[tuple[_Node, tuple[_Node, ...] | None]]:
    """Traverse the tree depth-first post-order"""
    match node:
        case _IndexNode():
            _parents = (node,) if parents is None else parents + (node,)
            for child in node.children:
                yield from _iter_nodes_with_parents(child, _parents)
            yield node, parents
        case _TerminalNode():
            yield node, parents


def _short_summary(description: str | None) -> str | None:
    if description is None or len(description) <= SHORT_SUMMARY_TRUNCATION_LENGTH:
        return description
    return description[: SHORT_SUMMARY_TRUNCATION_LENGTH - 4] + " ..."


def _extract_parser_config(parser: ArgumentParser) -> dict[str, Any]:
    return {k: v for k, v in vars(parser).items() if not k.startswith("_")}
