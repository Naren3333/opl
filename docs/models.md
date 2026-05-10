# Models

Models are lightweight dynamic objects. They support properties, methods, constructors, and `captain` binding.

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

Expected output:

```text
Luffy
Luffy
```

## Constructors

If a model defines `spawn`, it runs automatically when the model is called:

```opl
model Ship:
    dfruit spawn(name):
        captain.name = name

bounty sunny = Ship("Thousand Sunny")
say sunny.name
```

## Properties

Properties are dynamic:

```opl
bounty p = Pirate("Luffy")
p.bounty = 3000
say p.bounty
```

## Methods

Methods bind `captain` automatically:

```opl
model Counter:
    dfruit spawn():
        captain.value = 0

    dfruit next():
        captain.value = captain.value + 1
        return captain.value

bounty c = Counter()
say c.next()
say c.next()
```
