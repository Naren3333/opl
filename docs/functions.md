# Functions

Functions are declared with `dfruit` in pirate syntax or `fn` in core syntax.

```opl
dfruit add(a, b):
    return a + b

say add(2, 3)
```

Expected output:

```text
5
```

## Core Syntax

```opl
fn add(a, b) {
    return a + b
}

print(add(2, 3))
```

## First-Class Functions

Functions can be assigned to variables and called later:

```opl
dfruit greet():
    say "hello"

bounty f = greet
f()
```

## Closures

Inner functions can capture variables from their outer scope:

```opl
dfruit make_counter():
    bounty x = 0

    dfruit next():
        x = x + 1
        return x

    return next

bounty counter = make_counter()

say counter()
say counter()
```

Expected output:

```text
1
2
```

## Recursion

```opl
dfruit countdown(x):
    if x > 0:
        say x
        return countdown(x - 1)

    return 0

countdown(3)
```
