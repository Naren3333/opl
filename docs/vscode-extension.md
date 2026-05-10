# VSCode Extension

The OPL VSCode extension provides editor support for `.opl` files.

Install it from the [VSCode Marketplace](https://marketplace.visualstudio.com/items?itemName=Naren-SMU.opl-language).

## Features

- `.opl` file association
- OPL file icon
- Syntax highlighting
- Snippets
- Autocomplete
- Diagnostics
- Hover information
- Go to definition
- Document and workspace symbols
- Run current file button
- Debug current file button
- DAP debugger integration

## Runtime Requirement

The extension expects the OPL runtime to be installed:

```bash
pip install oplang
```

Verify:

```bash
opl --version
```

## Quick Editor Flow

1. Install the runtime with `pip install oplang`.
2. Install the VSCode extension.
3. Open an `.opl` file.
4. Use the editor Run or Debug button.
