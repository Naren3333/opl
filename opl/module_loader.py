import os

from opl import lexer, parser, source as source_tools, stdlib_bindings
from opl.ast import FunctionDeclaration, LetStatement, ModelDeclaration
from opl.errors import OPLError
from opl.interpreter import Environment, Interpreter, create_global_env


class ModuleLoader:
    def __init__(self, base_dir=None):
        self.base_dir = os.path.abspath(base_dir or os.getcwd())
        self.loading = []
        self.cache = {}

    def import_module(self, module_name, target_env, node):
        if stdlib_bindings.has_stdlib_module(module_name):
            target_env.define(module_name, stdlib_bindings.create_stdlib_module(module_name))
            return

        path = self.resolve(module_name)

        if path in self.loading:
            raise OPLError(
                "OPL-007",
                "Import Error",
                f"Circular import detected for '{module_name}'",
                node.line,
                node.column,
                type(node).__name__,
            )

        if path not in self.cache:
            self.cache[path] = self.load_module(module_name, path, node)

        for name, value in self.cache[path].items():
            target_env.define(name, value)

    def load_module(self, module_name, path, node):
        if not os.path.exists(path):
            raise OPLError(
                "OPL-007",
                "Import Error",
                f"Module '{module_name}' not found",
                node.line,
                node.column,
                type(node).__name__,
            )

        self.loading.append(path)
        previous_base_dir = self.base_dir
        self.base_dir = os.path.dirname(path)

        try:
            with open(path, "r", encoding="utf-8-sig") as file:
                source = file.read()

            source = source_tools.normalize_source(source)
            tokens = lexer.tokenize(source)
            program = parser.parse(tokens)
            module_env = create_global_env()
            Interpreter(self).eval(program, module_env)
            return exported_values(program, module_env)
        except OPLError:
            raise
        except OSError as error:
            raise OPLError(
                "OPL-007",
                "Import Error",
                str(error),
                node.line,
                node.column,
                type(node).__name__,
            )
        finally:
            self.base_dir = previous_base_dir
            self.loading.pop()

    def resolve(self, module_name):
        return os.path.abspath(os.path.join(self.base_dir, module_name + ".opl"))


def run_program(program, base_dir=None):
    loader = ModuleLoader(base_dir)
    env = create_global_env()
    Interpreter(loader).eval(program, env)
    return env


def exported_values(program, env):
    exports = {}

    for statement in program.statements:
        if isinstance(statement, (FunctionDeclaration, LetStatement, ModelDeclaration)):
            exports[statement.name] = env.values[statement.name]

    return exports


