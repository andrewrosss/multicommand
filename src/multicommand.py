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
    root = _create_directory_node(command_pkg, prog, parser_variable)
    _populate_subparsers_actions(root)
    _link_parsers(root)
    return root.parser


def _node_factory() -> list[_Node]:
    """default_factory of _DirectoryNode. (For the type checker)"""
    return []


@dataclass
class _FileNode:
    name: str
    parser: ArgumentParser


@dataclass
class _DirectoryNode:
    name: str
    parser: ArgumentParser
    subparsers_action: _SubParsersAction[ArgumentParser] | None = None
    children: list[_Node] = field(
        init=False,
        repr=False,
        default_factory=_node_factory,
    )


_Node = _DirectoryNode | _FileNode


# The next three functions work together to build the parser tree.
#
# They're a little interdependent (i.e, they assume that they will
# be called in a certain order). Separating them makes the code
# easier to read (IMO), and TBH the code is short and they're
# marked as "private" anyway.
#
# They could be shoved into _DirectoryNode as static methods, maybe with
# some kind of "build" classmethod on _DirectoryNode that calls them
# in order, but I feel like a class with a bunch longer methods seems
# less clear than these standalone functions. Plus, I just don't like
# the extra level of indentation or extra syntactic cruft :P


def _create_directory_node(
    pkg: ModuleType,
    name: str,
    parser_variable: str,
) -> _DirectoryNode:
    """Recursively build a node tree from a package's modules.

    This function assumes that it will receive a package module (directory node).
    """
    dir_parser = getattr(pkg, parser_variable, ArgumentParser())
    dir_node = _DirectoryNode(name, dir_parser)

    for info in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        *_, suffix = info.name.split(".")
        mod = import_module(info.name)

        if info.ispkg:
            # package (directory parser) -> build this subtree and add it as a child
            node = _create_directory_node(mod, suffix, parser_variable)
            dir_node.children.append(node)
        else:
            # module (file parser) -> add as a file child
            file_parser = getattr(mod, parser_variable, None)
            if isinstance(file_parser, ArgumentParser):
                dir_node.children.append(_FileNode(suffix, file_parser))

    return dir_node


def _populate_subparsers_actions(node: _DirectoryNode):
    """Add subparsers actions to directory nodes that have children.

    This must be done before linking parsers, as linking requires the
    subparsers action to be present.

    Standalone, this function looks weird, but it expects to be called after
    the entire tree has been built (i.e., after _create_directory_node), and
    before _link_parsers.
    """
    for n, _ in _iter_directory_nodes(node):
        if n.children:
            # if there are children, create a subparsers action
            #
            # note: we only do this if there are children, if there
            #       aren't, it's theoretically possible to have a
            #       directory parser act as a file parser,
            #       and in that case, we don't want to add a subparsers action.
            n.subparsers_action = _get_or_add_subparsers(
                n.parser, description=" ", metavar="command"
            )


def _link_parsers(node: _DirectoryNode) -> None:
    """Register child parsers with their parent's subparsers action.

    This function is expected to be called after _populate_subparsers_actions.
    """
    for dir_node, parents in _iter_directory_nodes(node):
        for child in dir_node.children:
            if not dir_node.subparsers_action:
                continue  # should not happen if _populate_subparsers_actions was called

            intermediate = [n.name for n in parents] if parents else []
            prog = " ".join((*intermediate, dir_node.name, child.name))
            parser_config = _extract_parser_config(child.parser)
            parser_config["prog"] = prog
            parser_config["help"] = _short_summary(child.parser.description)
            parser_config["add_help"] = False
            dir_node.subparsers_action.add_parser(
                child.name, parents=[child.parser], **parser_config
            )


def _iter_directory_nodes(
    node: _DirectoryNode,
) -> Iterator[tuple[_DirectoryNode, list[_Node] | None]]:
    """Yield only DirectoryNode items from the tree traversal."""
    for n, parents in _iter_nodes_with_parents(node):
        match n:
            case _DirectoryNode():
                yield n, parents
            case _FileNode():
                continue


def _iter_nodes_with_parents(
    node: _Node,
    parents: list[_Node] | None = None,
) -> Iterator[tuple[_Node, list[_Node] | None]]:
    """Traverse the tree depth-first post-order"""
    match node:
        case _DirectoryNode():
            _parents: list[_Node] = [node] if parents is None else parents + [node]
            for child in node.children:
                yield from _iter_nodes_with_parents(child, _parents)
            yield node, parents
        case _FileNode():
            yield node, parents


def _get_or_add_subparsers(
    parser: ArgumentParser, **kwargs: Any
) -> _SubParsersAction[ArgumentParser]:
    """Get existing subparsers action or create one if none exists."""
    if parser._subparsers is not None:
        # already has subparsers - find and return the action
        #
        # note: we need to do this because if `add_subparsers` has already been
        #       called (e.g. by userland code), calling it again will raise an exception
        #       see: https://github.com/python/cpython/blob/1f16df4bfe5cfbe4ac40cc9c6d15f44bcfd99a64/Lib/argparse.py#L1873-L1874
        for action in parser._actions:
            if isinstance(action, _SubParsersAction):
                return action  # type: ignore[return-value]
        # should never reach here if _subparsers is set ...
        raise RuntimeError("_subparsers set but no _SubParsersAction found")

    # no subparsers yet - create one
    return parser.add_subparsers(**kwargs)


def _short_summary(description: str | None) -> str | None:
    if description is None or len(description) <= SHORT_SUMMARY_TRUNCATION_LENGTH:
        return description
    return description[: SHORT_SUMMARY_TRUNCATION_LENGTH - 4] + " ..."


def _extract_parser_config(parser: ArgumentParser) -> dict[str, Any]:
    return {k: v for k, v in vars(parser).items() if not k.startswith("_")}
