# Bytecode VM

OPL includes both an AST interpreter and a stack-based bytecode VM. The interpreter remains the reference runtime, while the VM provides compiled execution.

## Run With The VM

```bash
opl run file.opl --vm
```

## Build Bytecode

```bash
opl build file.opl
```

This produces:

```text
file.oplb
```

## Run Bytecode

```bash
opl run file.oplb --vm
```

## Inspect Bytecode

```bash
opl inspect file.oplb
```

## Debug Bytecode Output

```bash
opl run file.opl --vm --debug-bytecode
```

The VM supports the major language features, including variables, functions, closures, collections, models, imports, and standard library calls.
