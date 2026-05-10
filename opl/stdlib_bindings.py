import math
import os
import random
from datetime import datetime

from opl.errors import OPLError
from opl.interpreter import BuiltinFunction, NativeModule


STDLIB_MODULES = {
    "math": {
        "abs": (1, lambda runtime, args, node: abs(number_arg(runtime, args[0], node))),
        "min": (2, lambda runtime, args, node: min_numbers(runtime, args, node)),
        "max": (2, lambda runtime, args, node: max_numbers(runtime, args, node)),
        "sqrt": (1, lambda runtime, args, node: sqrt(runtime, args[0], node)),
    },
    "string": {
        "upper": (1, lambda runtime, args, node: string_arg(runtime, args[0], node).upper()),
        "lower": (1, lambda runtime, args, node: string_arg(runtime, args[0], node).lower()),
        "split": (2, lambda runtime, args, node: split(runtime, args, node)),
    },
    "random": {
        "int": (2, lambda runtime, args, node: random_int(runtime, args, node)),
    },
    "time": {
        "now": (0, lambda runtime, args, node: datetime.now().isoformat(timespec="seconds")),
    },
    "io": {
        "read": (1, lambda runtime, args, node: read_file(runtime, args[0], node)),
        "write": (2, lambda runtime, args, node: write_file(runtime, args, node)),
    },
}


def has_stdlib_module(name):
    return name in STDLIB_MODULES


def create_stdlib_module(name):
    functions = {}
    for function_name, (arity, action) in STDLIB_MODULES[name].items():
        functions[function_name] = BuiltinFunction(f"{name}.{function_name}", arity, action)
    return NativeModule(name, functions)


def stdlib_function_names(name):
    return list(STDLIB_MODULES.get(name, {}).keys())


def number_arg(runtime, value, node):
    if isinstance(value, int):
        return value
    raise runtime.runtime_error(node, "Expected number argument")


def string_arg(runtime, value, node):
    if isinstance(value, str):
        return value
    raise runtime.runtime_error(node, "Expected string argument")


def min_numbers(runtime, args, node):
    return min(number_arg(runtime, args[0], node), number_arg(runtime, args[1], node))


def max_numbers(runtime, args, node):
    return max(number_arg(runtime, args[0], node), number_arg(runtime, args[1], node))


def sqrt(runtime, value, node):
    value = number_arg(runtime, value, node)
    if value < 0:
        raise runtime.runtime_error(node, "sqrt expects a non-negative number")
    result = math.sqrt(value)
    if result.is_integer():
        return int(result)
    return result


def split(runtime, args, node):
    text = string_arg(runtime, args[0], node)
    separator = string_arg(runtime, args[1], node)
    return text.split(separator)


def random_int(runtime, args, node):
    minimum = number_arg(runtime, args[0], node)
    maximum = number_arg(runtime, args[1], node)
    if minimum > maximum:
        raise runtime.runtime_error(node, "random.int minimum cannot be greater than maximum")
    return random.randint(minimum, maximum)


def read_file(runtime, path, node):
    safe_path = resolve_safe_path(runtime, path, node)
    try:
        with open(safe_path, "r", encoding="utf-8") as file:
            return file.read()
    except OSError as error:
        raise runtime.runtime_error(node, f"File read failed: {error}")


def write_file(runtime, args, node):
    safe_path = resolve_safe_path(runtime, args[0], node)
    text = string_arg(runtime, args[1], node)
    try:
        with open(safe_path, "w", encoding="utf-8") as file:
            file.write(text)
    except OSError as error:
        raise runtime.runtime_error(node, f"File write failed: {error}")
    return None


def resolve_safe_path(runtime, path, node):
    path = string_arg(runtime, path, node)
    if os.path.isabs(path):
        raise runtime.runtime_error(node, "io paths must be relative")

    base_dir = os.getcwd()
    if runtime.module_loader:
        base_dir = runtime.module_loader.base_dir

    safe_base = os.path.abspath(base_dir)
    full_path = os.path.abspath(os.path.join(safe_base, path))

    if full_path != safe_base and not full_path.startswith(safe_base + os.sep):
        raise runtime.runtime_error(node, "io path escapes project directory")

    return full_path
