# Quickstart

## Install

From PyPI:

```powershell
python -m pip install oplang
```

From this repository for local development:

```powershell
python -m pip install -e .
```

After installation, the CLI command is:

```powershell
opl --version
```

## First Program

Create `hello.opl`:

```opl
bounty name = "Luffy"
say name
```

Run it:

```powershell
opl run hello.opl
```

Expected output:

```text
Luffy
```

## Check Code

Validate a file without running it:

```powershell
opl check hello.opl
```

## Format Code

Format core OPL syntax:

```powershell
opl format hello.opl
```

## REPL

Start an interactive session:

```powershell
opl repl
```

Example:

```opl
>>> bounty x = 5
>>> say x
5
```

## Bytecode VM

Run through the VM:

```powershell
opl run hello.opl --vm
```

Build a compiled bytecode file:

```powershell
opl build hello.opl
```

This creates:

```text
hello.oplb
```

Run compiled bytecode:

```powershell
opl run hello.oplb --vm
```

Inspect bytecode:

```powershell
opl inspect hello.oplb
```

## Debugging

Launch the VM debugger:

```powershell
opl debug hello.opl
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
