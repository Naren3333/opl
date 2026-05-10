# Language Basics

OPL supports both core syntax and pirate syntax inside `.opl` files. The pirate syntax is concise and beginner-friendly, while the core syntax is what the compiler pipeline executes after frontend normalization.

## Variables

Pirate syntax:

```opl
bounty x = 10
say x
```

Core syntax:

```opl
let x = 10
print(x)
```

## Control Flow

```opl
let x = 5

if x > 3 {
    print("large")
}

while x > 0 {
    print(x)
    x = x - 1
}
```

## Functions

```opl
dfruit add(a, b):
    return a + b

bounty result = add(2, 3)
say result
```

Functions are first-class values:

```opl
dfruit greet():
    say "hello"

bounty f = greet
f()
```

## Closures

```opl
fn counter() {
    let n = 0

    fn next() {
        n = n + 1
        return n
    }

    return next
}

let c = counter()
print(c())
print(c())
```

Expected output:

```text
1
2
```

## Collections

Lists:

```opl
bounty nums = [1, 2, 3]
append(nums, 4)

for item in nums:
    say item
```

Maps:

```opl
bounty pirate = {
    "name": "Luffy",
    "bounty": 3000
}

say pirate["name"]
```

## Models

Models are lightweight dynamic objects.

```opl
model Pirate:
    dfruit spawn(name):
        captain.name = name

    dfruit greet():
        say captain.name

bounty luffy = Pirate("Luffy")
luffy.greet()
say luffy.name
```

## Imports

Imports load local `.opl` files or standard library modules.

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
