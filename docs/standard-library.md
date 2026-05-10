# Standard Library

OPL includes first-party standard library modules. Import them by name:

```opl
import math
say math.sqrt(25)
```

Standard library imports resolve automatically before local project modules.

## math

```opl
import math

say math.abs(-5)
say math.min(3, 7)
say math.max(3, 7)
say math.sqrt(25)
```

## string

```opl
import string

say string.upper("luffy")
say string.lower("ZORO")

bounty parts = string.split("one,two,three", ",")
say parts[0]
```

## random

```opl
import random

say random.int(1, 10)
```

## time

```opl
import time

say time.now()
```

## io

The `io` module reads and writes relative paths only.

```opl
import io

io.write("note.txt", "hello")
say io.read("note.txt")
```

