import os

from opl import lexer, parser, source as source_tools, stdlib_bindings
from opl.ast import (
    AssignmentStatement,
    BinaryExpression,
    ExpressionStatement,
    ForStatement,
    FunctionCall,
    FunctionDeclaration,
    Identifier,
    IfStatement,
    IndexAccess,
    IndexAssignment,
    ImportStatement,
    LetStatement,
    ListLiteral,
    MapLiteral,
    MethodCall,
    ModelDeclaration,
    PrintStatement,
    Program,
    PropertyAccess,
    PropertyAssignment,
    ReturnStatement,
    UnaryExpression,
    WhileStatement,
)
from opl.errors import OPLError


BUILTINS = {"len", "append", "keys"}


class Diagnostic:
    def __init__(self, message, severity, line, column, code):
        self.message = message
        self.severity = severity
        self.line = line
        self.column = column
        self.code = code

    def to_dict(self):
        return {
            "message": self.message,
            "severity": self.severity,
            "line": self.line,
            "column": self.column,
            "code": self.code,
        }


class Symbol:
    def __init__(self, kind, model_name=None, module_name=None):
        self.kind = kind
        self.model_name = model_name
        self.module_name = module_name


class ModelInfo:
    def __init__(self, methods=None, properties=None):
        self.methods = set(methods or [])
        self.properties = set(properties or [])


class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.values = {}

    def define(self, name, symbol):
        self.values[name] = symbol

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        return None


def check_file(file_path):
    try:
        source_tools.validate_path(file_path)
        with open(file_path, "r", encoding="utf-8-sig") as file:
            source = file.read()
        return check_source(source, os.path.dirname(os.path.abspath(file_path)))
    except OPLError as error:
        return [from_opl_error(error)]
    except OSError as error:
        return [Diagnostic(str(error), "error", 1, 1, "OPL-D004")]


def check_source(source, base_dir=None):
    try:
        normalized = source_tools.normalize_source(source)
        tokens = lexer.tokenize(normalized)
        program = parser.parse(tokens)
        return analyze(program, base_dir)
    except OPLError as error:
        return [from_opl_error(error)]


def analyze(program, base_dir=None):
    analyzer = Analyzer(base_dir)
    return analyzer.analyze(program)


def from_opl_error(error):
    return Diagnostic(error.message, "error", error.line, error.column, error.code)


class Analyzer:
    def __init__(self, base_dir=None):
        self.base_dir = os.path.abspath(base_dir or os.getcwd())
        self.diagnostics = []
        self.models = {}
        self.loading = []
        self.module_cache = {}

    def analyze(self, program):
        scope = Scope()
        for name in BUILTINS:
            scope.define(name, Symbol("builtin"))

        self.predeclare(program, scope)
        self.visit_program(program, scope)
        return self.diagnostics

    def predeclare(self, program, scope):
        for statement in program.statements:
            if isinstance(statement, FunctionDeclaration):
                scope.define(statement.name, Symbol("function"))
            elif isinstance(statement, ModelDeclaration):
                self.models[statement.name] = self.collect_model_info(statement)
                scope.define(statement.name, Symbol("model", statement.name))

    def collect_model_info(self, node):
        info = ModelInfo(method.name for method in node.methods)
        for method in node.methods:
            self.collect_captain_properties(method.body, info)
        return info

    def collect_captain_properties(self, statements, info):
        for statement in statements:
            if (
                isinstance(statement, PropertyAssignment)
                and isinstance(statement.target.object_expr, Identifier)
                and statement.target.object_expr.name == "captain"
            ):
                info.properties.add(statement.target.name)
            for child in self.child_statements(statement):
                self.collect_captain_properties(child, info)

    def visit_program(self, program, scope):
        for statement in program.statements:
            self.visit(statement, scope, in_function=False, current_model=None)

    def visit(self, node, scope, in_function, current_model):
        if isinstance(node, Program):
            self.visit_program(node, scope)
        elif isinstance(node, LetStatement):
            self.visit(node.value, scope, in_function, current_model)
            scope.define(node.name, self.infer_symbol(node.value, scope))
        elif isinstance(node, AssignmentStatement):
            if not scope.get(node.name):
                self.report(node, f"Undefined variable '{node.name}'", "OPL-D001")
            self.visit(node.value, scope, in_function, current_model)
        elif isinstance(node, FunctionDeclaration):
            self.visit_function(node, scope, current_model=None)
        elif isinstance(node, ModelDeclaration):
            self.visit_model(node, scope)
        elif isinstance(node, ReturnStatement):
            if not in_function:
                self.report(node, "return used outside function", "OPL-D005")
            self.visit(node.value, scope, in_function, current_model)
        elif isinstance(node, ImportStatement):
            self.visit_import(node, scope)
        elif isinstance(node, PrintStatement):
            self.visit(node.value, scope, in_function, current_model)
        elif isinstance(node, ExpressionStatement):
            self.visit(node.expression, scope, in_function, current_model)
        elif isinstance(node, IfStatement):
            self.visit(node.condition, scope, in_function, current_model)
            self.visit_block(node.body, Scope(scope), in_function, current_model)
        elif isinstance(node, WhileStatement):
            self.visit(node.condition, scope, in_function, current_model)
            self.visit_block(node.body, Scope(scope), in_function, current_model)
        elif isinstance(node, ForStatement):
            self.visit(node.iterable, scope, in_function, current_model)
            loop_scope = Scope(scope)
            loop_scope.define(node.name, Symbol("variable"))
            self.visit_block(node.body, Scope(loop_scope), in_function, current_model)
        elif isinstance(node, BinaryExpression):
            self.visit(node.left, scope, in_function, current_model)
            self.visit(node.right, scope, in_function, current_model)
        elif isinstance(node, UnaryExpression):
            self.visit(node.right, scope, in_function, current_model)
        elif isinstance(node, Identifier):
            self.visit_identifier(node, scope, current_model)
        elif isinstance(node, FunctionCall):
            self.visit_function_call(node, scope, in_function, current_model)
        elif isinstance(node, ListLiteral):
            for element in node.elements:
                self.visit(element, scope, in_function, current_model)
        elif isinstance(node, MapLiteral):
            for key, value in node.entries:
                self.visit(key, scope, in_function, current_model)
                self.visit(value, scope, in_function, current_model)
        elif isinstance(node, IndexAccess):
            self.visit(node.object_expr, scope, in_function, current_model)
            self.visit(node.index, scope, in_function, current_model)
        elif isinstance(node, IndexAssignment):
            self.visit(node.target, scope, in_function, current_model)
            self.visit(node.value, scope, in_function, current_model)
        elif isinstance(node, PropertyAccess):
            self.visit_property_access(node, scope, in_function, current_model)
        elif isinstance(node, PropertyAssignment):
            self.visit_property_assignment(node, scope, in_function, current_model)
        elif isinstance(node, MethodCall):
            self.visit_method_call(node, scope, in_function, current_model)

    def visit_block(self, statements, scope, in_function, current_model):
        self.predeclare(Program(statements), scope)
        for statement in statements:
            self.visit(statement, scope, in_function, current_model)

    def visit_function(self, node, scope, current_model):
        function_scope = Scope(scope)
        if current_model:
            function_scope.define("captain", Symbol("instance", current_model))
        for parameter in node.parameters:
            function_scope.define(parameter, Symbol("variable"))
        self.visit_block(node.body, function_scope, in_function=True, current_model=current_model)

    def visit_model(self, node, scope):
        self.models[node.name] = self.collect_model_info(node)
        scope.define(node.name, Symbol("model", node.name))
        for method in node.methods:
            self.visit_function(method, scope, current_model=node.name)

    def visit_import(self, node, scope):
        if stdlib_bindings.has_stdlib_module(node.module_name):
            scope.define(node.module_name, Symbol("stdlib", module_name=node.module_name))
            return

        path = os.path.abspath(os.path.join(self.base_dir, node.module_name + ".opl"))
        if path in self.loading:
            self.report(node, f"Circular import detected for '{node.module_name}'", "OPL-D007")
            return
        if not os.path.exists(path):
            self.report(node, f"Module '{node.module_name}' not found", "OPL-D007")
            return

        if path not in self.module_cache:
            self.loading.append(path)
            previous_base = self.base_dir
            self.base_dir = os.path.dirname(path)
            try:
                with open(path, "r", encoding="utf-8-sig") as file:
                    source = source_tools.normalize_source(file.read())
                program = parser.parse(lexer.tokenize(source))
                module_scope = Scope()
                for name in BUILTINS:
                    module_scope.define(name, Symbol("builtin"))
                self.predeclare(program, module_scope)
                self.visit_program(program, module_scope)
                self.module_cache[path] = {
                    "symbols": exported_symbols(program, module_scope),
                    "models": dict(self.models),
                }
            except OPLError as error:
                self.diagnostics.append(from_opl_error(error))
                self.module_cache[path] = {"symbols": {}, "models": {}}
            finally:
                self.base_dir = previous_base
                self.loading.pop()

        for name, symbol in self.module_cache[path]["symbols"].items():
            scope.define(name, symbol)
        self.models.update(self.module_cache[path]["models"])

    def visit_identifier(self, node, scope, current_model):
        symbol = scope.get(node.name)
        if symbol:
            return
        if node.name == "captain":
            self.report(node, "captain is only available inside methods", "OPL-D001")
            return
        self.report(node, f"Undefined variable '{node.name}'", "OPL-D001")

    def visit_function_call(self, node, scope, in_function, current_model):
        for argument in node.arguments:
            self.visit(argument, scope, in_function, current_model)

        if isinstance(node.callee, Identifier):
            symbol = scope.get(node.callee.name)
            if not symbol:
                kind = "model" if node.callee.name[:1].isupper() else "function"
                self.report(node, f"Undefined {kind} '{node.callee.name}'", "OPL-D002")
                return
            if symbol.kind not in ("function", "model", "builtin", "variable"):
                code = "OPL-D003" if node.callee.name[:1].isupper() else "OPL-D002"
                message = (
                    f"Invalid model constructor '{node.callee.name}'"
                    if code == "OPL-D003"
                    else f"Undefined function '{node.callee.name}'"
                )
                self.report(node, message, code)
            return

        self.visit(node.callee, scope, in_function, current_model)

    def visit_property_access(self, node, scope, in_function, current_model):
        self.visit(node.object_expr, scope, in_function, current_model)
        if isinstance(node.object_expr, Identifier):
            symbol = scope.get(node.object_expr.name)
            if symbol and symbol.kind == "stdlib":
                names = stdlib_bindings.stdlib_function_names(symbol.module_name)
                if node.name not in names:
                    self.report(node, f"Undefined stdlib member '{node.name}'", "OPL-D004")
                return

        model_name = self.model_for_expression(node.object_expr, scope, current_model)
        if not model_name or model_name not in self.models:
            return
        if node.name not in self.models[model_name].properties:
            self.report(node, f"Undefined property '{node.name}'", "OPL-D004")

    def visit_property_assignment(self, node, scope, in_function, current_model):
        self.visit(node.target.object_expr, scope, in_function, current_model)
        self.visit(node.value, scope, in_function, current_model)

    def visit_method_call(self, node, scope, in_function, current_model):
        self.visit(node.object_expr, scope, in_function, current_model)
        for argument in node.arguments:
            self.visit(argument, scope, in_function, current_model)

        if isinstance(node.object_expr, Identifier):
            symbol = scope.get(node.object_expr.name)
            if symbol and symbol.kind == "stdlib":
                names = stdlib_bindings.stdlib_function_names(symbol.module_name)
                if node.name not in names:
                    self.report(node, f"Undefined stdlib function '{node.name}'", "OPL-D004")
                return

        model_name = self.model_for_expression(node.object_expr, scope, current_model)
        if not model_name or model_name not in self.models:
            return
        if node.name not in self.models[model_name].methods:
            self.report(node, f"Undefined method '{node.name}'", "OPL-D004")

    def model_for_expression(self, node, scope, current_model):
        if isinstance(node, Identifier):
            if node.name == "captain":
                return current_model
            symbol = scope.get(node.name)
            if symbol and symbol.kind == "instance":
                return symbol.model_name
        return None

    def infer_symbol(self, expression, scope):
        if (
            isinstance(expression, FunctionCall)
            and isinstance(expression.callee, Identifier)
        ):
            callee = scope.get(expression.callee.name)
            if callee and callee.kind == "model":
                return Symbol("instance", callee.model_name)
        return Symbol("variable")

    def child_statements(self, statement):
        if isinstance(statement, (IfStatement, WhileStatement, ForStatement)):
            return [statement.body]
        return []

    def report(self, node, message, code, severity="error"):
        self.diagnostics.append(
            Diagnostic(message, severity, node.line, node.column, code)
        )


def exported_symbols(program, scope):
    symbols = {}
    for statement in program.statements:
        if isinstance(statement, (FunctionDeclaration, LetStatement, ModelDeclaration)):
            symbol = scope.get(statement.name)
            if symbol:
                symbols[statement.name] = symbol
    return symbols
