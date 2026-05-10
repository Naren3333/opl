# OPL Documentation

OPL, the One Piece Language, is a lightweight scripting language with a readable pirate-flavored syntax and a real runtime behind it.

It includes an AST interpreter, a stack-based bytecode VM, compiled `.oplb` files, closures, models, collections, modules, a standard library, CLI tooling, a debugger, LSP support, and a VSCode extension.

```opl
bounty x = 5
say x + 1

dfruit add(a, b):
    return a + b

say add(2, 3)
```

Expected output:

```text
6
5
```

## Install

Install OPL from PyPI:

```bash
pip install oplang
```

Then run an `.opl` file:

```bash
opl run hello.opl
```

## Project Links

- [GitHub repository](https://github.com/Naren3333/opl)
- [PyPI package](https://pypi.org/project/oplang/)
- [VSCode Marketplace extension](https://marketplace.visualstudio.com/items?itemName=Naren-SMU.opl-language)

## What To Read Next

- [Installation](installation.md) explains the runtime, CLI, and editor setup.
- [Quickstart](quickstart.md) gets you from a first file to running bytecode.
- [Syntax](syntax.md) covers the OPL language surface.
- [Playground](playground.md) provides a copyable browser-friendly starter example.
