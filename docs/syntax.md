# Syntax

OPL supports both core syntax and pirate syntax inside `.opl` files. Pirate syntax is concise and user-facing; core syntax is the normalized form used by the compiler pipeline.

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

## Print

```opl
say "hello"
```

Core syntax:

```opl
print("hello")
```

## Conditionals

```opl
if x > 3:
    say "large"
```

Core syntax:

```opl
if x > 3 {
    print("large")
}
```

## While Loops

```opl
bounty x = 3

while x > 0:
    say x
    x = x - 1
```

## For-In Loops

```opl
bounty crew = ["Luffy", "Zoro", "Nami"]

for member in crew:
    say member
```

## Expressions

OPL supports arithmetic and comparisons:

```opl
say 1 + 2 * 3
say 10 > 5
say 4 != 2
```

## Comments

Single-line comments use `//`:

```opl
// This is a comment.
bounty x = 5
```
