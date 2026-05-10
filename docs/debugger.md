# Debugger

OPL includes a VM debugger for stepping through bytecode execution and inspecting runtime state.

## Start The Debugger

```bash
opl debug file.opl
```

You can also debug compiled bytecode:

```bash
opl debug file.oplb
```

## Common Commands

```text
step
continue
break 12
break file.opl:5
stack
locals
inspect name
quit
```

## VM Debug Mode

```bash
opl run file.opl --vm --debug
```

Debug mode prints instruction traces, stack state, and source mapping where available.

## VSCode Debugging

The VSCode extension connects to the OPL Debug Adapter Protocol integration, so breakpoints and variable inspection work from the editor.
