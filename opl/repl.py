import os
import sys

from opl import interpreter, lexer, module_loader, parser
from opl.__version__ import __version__
from opl.errors import OPLError


def start():
    configure_output()

    print(f"OPL REPL v{__version__}")
    print("Type ':help' for commands")

    runtime = interpreter.Interpreter()
    loader = module_loader.ModuleLoader(os.getcwd())
    runtime.module_loader = loader
    env = interpreter.create_global_env()
    buffer = []
    input_index = 1

    while True:
        prompt = "... " if buffer else ">>> "

        try:
            line = input(prompt)
        except EOFError:
            print()
            return 0

        if not buffer and line.strip().startswith(":"):
            if handle_command(line.strip()):
                return 0
            continue

        buffer.append(line)

        if not is_complete(buffer):
            continue

        source = "\n".join(buffer)
        buffer = []

        if not source.strip():
            continue

        try:
            tokens = lexer.tokenize(source)
            program = parser.parse(tokens)
            runtime.eval(program, env)
        except OPLError as error:
            print_repl_error(error, input_index)
        except Exception as error:
            print(f"OPL-999 Internal Error\nREPL Line {input_index}\n\n{error}")

        input_index += 1


def is_complete(lines):
    source = "\n".join(lines)
    return brace_balance(source) == 0


def brace_balance(source):
    balance = 0
    in_string = False

    for char in source:
        if char == '"':
            in_string = not in_string
        elif not in_string and char == "{":
            balance += 1
        elif not in_string and char == "}":
            balance -= 1

    return balance


def print_repl_error(error, input_index):
    print(f"{error.code} {error.title}")
    print(f"REPL Line {input_index}")
    if error.node_type:
        print(f"Node: {error.node_type}")
    print()
    print(error.message)


def handle_command(command):
    if command == ":help":
        print("REPL commands:")
        print("  :help   Show this help")
        print("  :clear  Clear the screen")
        print("  :exit   Exit the REPL")
        return False
    if command == ":clear":
        print("\033c", end="")
        return False
    if command in (":exit", ":quit"):
        return True

    print(f"Unknown REPL command: {command}")
    print("Type ':help' for commands")
    return False


def configure_output():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
