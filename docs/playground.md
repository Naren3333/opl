# Playground

The hosted documentation is compatible with GitHub Pages, which is static hosting. That means the web playground is intentionally simple: edit and copy the sample code, then run it locally with the OPL CLI.

## Starter Program

```opl
bounty x = 5
say x + 1

dfruit add(a, b):
    return a + b

say add(2, 3)
```

Expected output:

```text
6
5
```

## Run Locally

Install OPL:

```bash
pip install oplang
```

Save the example as `app.opl`, then run:

```bash
opl run app.opl
```

## VM Mode

```bash
opl run app.opl --vm
```

## Compiled Mode

```bash
opl build app.opl
opl run app.oplb --vm
```
