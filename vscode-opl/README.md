# OPL Language Support

Professional VSCode support for OPL (One Piece Language), a lightweight programming language with pirate syntax, an AST interpreter, bytecode VM, diagnostics, and debugger tooling.

## Quickstart

1. Install the OPL runtime:

```powershell
python -m pip install oplang
```

2. Install this VSCode extension.

3. Open any `.opl` file.

4. Run from a terminal:

```powershell
opl run file.opl
```

5. Debug from VSCode with the included `Run OPL` launch configuration, or run:

```powershell
opl debug file.opl
```

## Features

- Syntax highlighting for `.opl` files
- Bracket auto-closing for `{}`, `[]`, and `()`
- Indentation support for functions, models, loops, and conditionals
- Snippets for common OPL patterns
- Autocomplete for functions, models, variables, methods, and standard library symbols
- Diagnostics for syntax and semantic issues
- Hover, go-to-definition, document symbols, and workspace symbols
- VSCode debugger integration with breakpoints, stepping, stack frames, and variables

## File Extension

OPL uses one official source file extension:

```text
.opl
```

## Example

Pirate syntax:

```opl
dfruit add(a, b):
    return a + b

bounty result = add(2, 3)
say result
```

Core syntax:

```opl
fn add(a, b) {
    return a + b
}

let result = add(2, 3)
print(result)
```

## Debugging

Use the default launch configuration:

```json
{
  "type": "opl",
  "request": "launch",
  "name": "Run OPL",
  "program": "${file}"
}
```

Set breakpoints in `.opl` files, press F5, step through execution, and inspect variables in the VSCode debugger panels.

## Requirements

This extension expects the OPL runtime tools to be available through Python:

```powershell
python -m pip install oplang
```

The runtime provides:

- `opl`
- `opl-lsp`
- `opl-dap`

If VSCode cannot find your Python installation, set `OPL_PYTHON` to the Python executable that has `oplang` installed.

## Snippets

- `dfruit` creates a function
- `model` creates a model with a `spawn` constructor
- `for` creates a for-in loop
- `if` creates an if statement

## Extension Development

For maintainers working on the extension internals:

- `OPL_LSP_PATH` can point to a local language server script.
- `OPL_DAP_PATH` can point to a local debug adapter script.
- Publish a patch release only after reviewing the Marketplace README:

```powershell
vsce publish patch
```
