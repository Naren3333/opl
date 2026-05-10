# Collections

OPL includes lists, maps, indexing, index assignment, and for-in loops.

## Lists

```opl
bounty nums = [1, 2, 3]
say nums[0]
```

## Append

```opl
bounty nums = [1, 2, 3]
append(nums, 4)

for item in nums:
    say item
```

## Maps

```opl
bounty pirate = {
    "name": "Luffy",
    "bounty": 3000
}

say pirate["name"]
```

## Index Assignment

```opl
bounty nums = [1, 2, 3]
nums[0] = 10
say nums[0]
```

```opl
bounty pirate = {
    "name": "Luffy"
}

pirate["name"] = "Zoro"
say pirate["name"]
```

## Built-Ins

```opl
len(value)
append(list, value)
keys(map)
```
