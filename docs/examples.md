# Examples

## Counter Closure

```opl
fn make_counter() {
    let x = 0

    fn next() {
        x = x + 1
        return x
    }

    return next
}

let counter = make_counter()

print(counter())
print(counter())
print(counter())
```

## Model

```opl
model Pirate:
    dfruit spawn(name, bounty_value):
        captain.name = name
        captain.bounty = bounty_value

    dfruit introduce():
        say captain.name
        say captain.bounty

bounty luffy = Pirate("Luffy", 3000)
luffy.introduce()
```

## Collections

```opl
bounty crew = ["Luffy", "Zoro", "Nami"]
append(crew, "Sanji")

for member in crew:
    say member
```

## Map Lookup

```opl
bounty pirate = {
    "name": "Luffy",
    "role": "captain"
}

say pirate["name"]
say pirate["role"]
```

## Standard Library

```opl
import math
import string

say math.sqrt(81)
say string.upper("going merry")
```
