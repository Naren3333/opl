# Installation

OPL is distributed on PyPI under the package name `oplang`. The installed command remains `opl`.

## Install From PyPI

```bash
pip install oplang
```

Verify the installation:

```bash
opl --version
```

## Local Development Install

From the repository root:

```bash
python -m pip install -e .
```

## CLI Commands

```bash
opl run file.opl
opl check file.opl
opl format file.opl
opl repl
opl build file.opl
opl inspect file.oplb
opl debug file.opl
```

## VSCode Extension

Install the OPL extension from the [VSCode Marketplace](https://marketplace.visualstudio.com/items?itemName=Naren-SMU.opl-language).

The extension provides:

- `.opl` file association
- Syntax highlighting
- Snippets
- Run and debug buttons
- LSP diagnostics, hover, definitions, symbols, and completions
- DAP debugger integration

## File Extensions

OPL source files use:

```text
.opl
```

Compiled bytecode files use:

```text
.oplb
```
