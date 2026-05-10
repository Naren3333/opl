# Modules and Imports

OPL modules are `.opl` files. Importing a module parses and executes it in its own environment, then exposes public symbols.

## Local Modules

`math_tools.opl`:

```opl
dfruit double(x):
    return x * 2
```

`main.opl`:

```opl
import math_tools
say double(21)
```

Expected output:

```text
42
```

## Standard Library Modules

Standard library modules are imported by name:

```opl
import math
say math.sqrt(25)
```

## Resolution Rules

Imports resolve:

1. Standard library modules
2. Local `.opl` files

OPL uses `.opl` as the official source extension.

## Circular Imports

Circular imports are detected and reported as structured OPL errors.
