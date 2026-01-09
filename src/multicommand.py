from __future__ import annotations

import pkgutil
import sys
from argparse import ArgumentParser
from argparse import _SubParsersAction  # type: ignore
from collections.abc import Iterator
from dataclasses import dataclass
from dataclasses import field
from importlib import import_module
from types import ModuleType
from typing import Any

__all__ = ("create_parser",)

# The name a variable that holds an ArgumentParser in each module.
PARSER_VARIABLE = "parser"

# The maximum length of a parser description to use as a short summary
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


def _node_factory() -> list[_Node]:
    """default_factory of _IndexNode. (For the type checker)"""
    return []


@dataclass
class _TerminalNode:
    name: str
    parser: ArgumentParser


@dataclass
class _IndexNode:
    name: str
    parser: ArgumentParser
    subparsers_action: _SubParsersAction[ArgumentParser] | None = None
    children: list[_Node] = field(
        init=False,
        repr=False,
        default_factory=_node_factory,
    )


_Node = _IndexNode | _TerminalNode


# The next three functions work together to build the parser tree.
#
# They're a little interdependent (i.e, they assume that they will
# be called in a certain order). Separating them makes the code
# easier to read (IMO), and TBH the code is short and they're
# marked as "private" anyway.
#
# They could be shoved into _IndexNode as static methods, maybe with
# some kind of "build" classmethod on _IndexNode that calls them
# in order, but I feel like a class with a bunch longer methods seems
# less clear than these standalone functions. Plus, I just don't like
# the extra level of indentation or extra syntactic cruft :P


def _create_index_node(
    pkg: ModuleType,
    name: str,
    parser_variable: str,
) -> _IndexNode:
    """Recursively build a node tree from a package's modules.

    This function assumes that it will recieve a package module (index node).
    """
    index_parser = getattr(pkg, parser_variable, ArgumentParser())
    index_node = _IndexNode(name, index_parser)

    for info in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        *_, suffix = info.name.split(".")
        mod = import_module(info.name)

        if info.ispkg:
            # package (index parser) -> build this subtree and add it as a child
            node = _create_index_node(mod, suffix, parser_variable)
            index_node.children.append(node)
        else:
            # module (terminal parser) -> add as a terminal child
            term_parser = getattr(mod, parser_variable, None)
            if isinstance(term_parser, ArgumentParser):
                index_node.children.append(_TerminalNode(suffix, term_parser))

    return index_node


def _populate_subparsers_actions(node: _IndexNode):
    """Add subparsers actions to index nodes that have children.

    This must be done before linking parsers, as linking requires the
    subparsers action to be present.

    Standalone, this function looks weird, but it expects to be called after
    the entire tree has been built (i.e., after _create_index_node), and
    before _link_parsers.
    """
    for n, _ in _iter_indexes(node):
        if n.children:
            # if there are children, create a subparsers action
            #
            # note: we only do this if there are children, if there
            #       aren't, it's theoretically possible to have an
            #       index parser (_index.py) act as a terminal parser,
            #       and in that case, we don't want to add a subparsers action.
            n.subparsers_action = n.parser.add_subparsers(
                description=" ", metavar="command"
            )


def _link_parsers(node: _IndexNode) -> None:
    """Register child parsers with their parent's subparsers action.

    This function is expected to be called after _populate_subparsers_actions.
    """
    for index, parents in _iter_indexes(node):
        for child in index.children:
            if not index.subparsers_action:
                continue  # should not happen if _populate_subparsers_actions was called

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
) -> Iterator[tuple[_IndexNode, list[_Node] | None]]:
    """Yield only IndexNode items from the tree traversal."""
    for n, parents in _iter_nodes_with_parents(node):
        match n:
            case _IndexNode():
                yield n, parents
            case _TerminalNode():
                continue


def _iter_nodes_with_parents(
    node: _Node,
    parents: list[_Node] | None = None,
) -> Iterator[tuple[_Node, list[_Node] | None]]:
    """Traverse the tree depth-first post-order"""
    match node:
        case _IndexNode():
            _parents: list[_Node] = [node] if parents is None else parents + [node]
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
