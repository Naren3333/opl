# OPL (One Piece Language)

OPL is a lightweight programming language with a readable pirate-flavored syntax and a real runtime behind it. It includes an AST interpreter, a stack-based bytecode VM, compiled `.oplb` files, closures, models, collections, modules, a standard library, CLI tooling, a debugger, LSP support, and a VSCode extension.

OPL source files use the `.opl` extension.

## Features

- Pirate syntax frontend with clean core OPL underneath
- AST interpreter for reference execution
- Stack-based VM with compiled bytecode support
- `.oplb` build and inspect workflow
- First-class functions and lexical closures
- Models, methods, properties, and `captain` binding
- Lists, maps, indexing, for-in loops, and collection built-ins
- Modules/imports and first-party standard library
- CLI, REPL, formatter, diagnostics, and debugger
- LSP-powered VSCode support with hover, definitions, symbols, completions, diagnostics, and DAP debugging

## Quickstart

Install OPL:

```powershell
pip install oplang
```

Create `hello.opl`:

```opl
bounty x = 5
say x + 1
```

Run it:

```powershell
opl run hello.opl
```

Expected output:

```text
6
```

## CLI

```powershell
opl --version
opl run file.opl
opl check file.opl
opl format file.opl
opl repl
```

Run on the VM:

```powershell
opl run file.opl --vm
```

Build bytecode:

```powershell
opl build file.opl
opl run file.oplb --vm
opl inspect file.oplb
```

## Debug

Launch the VM debugger:

```powershell
opl debug file.opl
```

Useful debugger commands:

```text
step
continue
stack
locals
inspect name
quit
```

## VSCode

The VSCode extension lives in `vscode-opl/`.

It provides:

- `.opl` file association
- Syntax highlighting
- Snippets
- Language configuration
- LSP diagnostics, hover, definitions, document symbols, workspace symbols, and completions
- DAP debugger integration

For local extension development:

```powershell
cd vscode-opl
npm install
```

Then open the extension folder in VSCode and run the extension host.

Marketplace packaging:

```powershell
npm install -g @vscode/vsce
vsce package
```

Publishing:

```powershell
vsce publish
```

## Documentation

- `docs/quickstart.md`
- `docs/language-basics.md`
- `docs/standard-library.md`
- `docs/examples.md`

## Website And Playground

The static website and local playground live in `website/`.

Start the local playground server:

```powershell
python website/playground_server.py --port 8787
```

Open:

```text
http://127.0.0.1:8787
```

## PyPI Release

Build distributions:

```powershell
python -m build
```

This creates:

```text
dist/oplang-*.whl
dist/oplang-*.tar.gz
```

Publish manually with Twine:

```powershell
python -m twine upload dist/*
```

Do not publish until the release artifacts have been inspected and tested.
