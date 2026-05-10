# OPL Language Support

VSCode support for OPL (One Piece Language), a lightweight programming language with pirate syntax, an AST interpreter, a bytecode VM, diagnostics, and debugger tooling.

Install the OPL command-line tools from PyPI:

```powershell
pip install oplang
```

## Features

- Syntax highlighting for `.opl` files
- Bracket auto-closing for `{}`, `[]`, and `()`
- Indentation support for `fn`, `model`, `if`, `while`, and `for`
- `//` line comments for editor ergonomics
- Snippets for common OPL patterns
- LSP-powered hover, definitions, outline, workspace symbols, completions, and diagnostics
- DAP debugger integration for `opl debug` style workflows inside VSCode

## File Extension

OPL uses a single official file extension:

```text
.opl
```

The extension associates editor support with `.opl` files only.

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

Run a file with the OPL CLI:

```powershell
opl run file.opl
```

Debug a file with the OPL debugger:

```powershell
opl debug file.opl
```

## Snippets

- `dfruit` creates a function
- `model` creates a model with a `spawn` constructor
- `for` creates a for-in loop
- `if` creates an if statement

## Language Server

The extension launches `opl-lsp`, a lightweight Language Server Protocol implementation that reuses the real OPL parser and diagnostics engine.

The same diagnostics are used by:

```powershell
opl check file.opl
```

Set `OPL_PYTHON` if the extension should use a specific Python executable. Set `OPL_LSP_PATH` to point at a custom `server.py` while developing the language server.

The first server is intentionally small, but it already follows standard JSON-RPC over stdio so it can grow into a fuller OPL language server later.

## Debugger

Create or use a launch configuration:

```json
{
  "type": "opl",
  "request": "launch",
  "name": "Run OPL",
  "program": "${file}"
}
```

Set breakpoints in `.opl` files, press F5, step through bytecode execution, and inspect variables from the VSCode debugger panels.

Set `OPL_DAP_PATH` to point at a custom debug adapter server while developing debugger support.

## Marketplace Packaging

Install the VSCode extension packaging tool:

```powershell
npm install -g @vscode/vsce
```

Build a local VSIX:

```powershell
vsce package
```

Publish when ready:

```powershell
vsce publish
```
