# Introduction

`multicommand` uses only the standard library and is ~100 lines of code (modulo comments and whitespace)

## Overview

Multicommand enables you to easily write CLIs with deeply nested commands using vanilla argparse. You provide it with a package, it searches that package for parsers (`argparse.ArgumentParser` objects), and connects, names, and converts those parsers into subcommands based on the package structure.

```text
        Package                       ->                    CLI


commands/unary/negate.py                            mycli unary negate ...
commands/binary/add.py                              mycli binary add ...
commands/binary/divide.py             ->            mycli binary divide ...
commands/binary/multiply.py                         mycli binary multiply ...
commands/binary/subtract.py                         mycli binary subtract ...
```

All it needs is for each module to define a module-level `parser` variable which points to an instance of `argparse.ArgumentParser`.

## Goals

- **Small** - The magic happens in a single file [multicommand.py](https://github.com/andrewrosss/multicommand/blob/master/src/multicommand.py)
- **Simple API** - Structure commands however you like, then call `multicommand.create_parser(...)`
- **Dependency-free** - You need python 3.10+, and that's it!

A happy by-product of `multicommand` being small and depedency-free is that it's even _portable_. Don't want add an additional dependency? Grab [multicommand.py](https://github.com/andrewrosss/multicommand/blob/master/src/multicommand.py), drop in in your project, and use it like any other module. (Not a huge fan of this option, but it can be done)

## Motivation

I like `argparse`. It's flexible, full-featured and it's part of the standard library, so if you have python you probably have argparse. I also like the "subcommand" pattern, i.e. one root command that acts as an entrypoint and subcommands to group related functionality. Of course, argparse can handle adding subcommands to parsers, but it's always felt a bit cumbersome, especially when there are many subcommands with lots of nesting.

If you've ever worked with technologies like `Next.js` or `oclif` (or even if you haven't) there's a duality between files and _objects_. For Next.js each file under `pages/` maps to a _webpage_, in oclif each module under `commands/` maps to a _CLI command_. And that's the basic premise for multicommand: A light-weight package that lets you write one parser per file, pretty much in isolation, and it handles the wiring, exploiting the duality between command structure and file system structure.
