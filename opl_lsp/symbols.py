import os
import re
from dataclasses import dataclass, field
from urllib.parse import unquote, urlparse

from opl import lexer, parser, source as source_tools, stdlib_bindings
from opl.ast import (
    AssignmentStatement,
    ExpressionStatement,
    ForStatement,
    FunctionCall,
    FunctionDeclaration,
    Identifier,
    IfStatement,
    ImportStatement,
    LetStatement,
    MethodCall,
    ModelDeclaration,
    PrintStatement,
    Program,
    PropertyAssignment,
    ReturnStatement,
    WhileStatement,
)
from opl.errors import OPLError


KIND_FILE = 1
KIND_MODULE = 2
KIND_CLASS = 5
KIND_METHOD = 6
KIND_FUNCTION = 12
KIND_VARIABLE = 13

COMPLETION_METHOD = 2
COMPLETION_FUNCTION = 3
COMPLETION_CLASS = 7
COMPLETION_VARIABLE = 6


@dataclass
class Symbol:
    name: str
    kind: str
    line: int
    column: int
    uri: str
    detail: str = ""
    parameters: list[str] = field(default_factory=list)
    container: str = ""

    def range(self):
        line = max(self.line - 1, 0)
        start = max(self.column - 1, 0)
        end = start + max(len(self.name), 1)
        return {
            "start": {"line": line, "character": start},
            "end": {"line": line, "character": end},
        }

    def location(self):
        return {"uri": self.uri, "range": self.range()}


@dataclass
class DocumentIndex:
    uri: str
    path: str
    source: str
    program: object | None = None
    symbols: list[Symbol] = field(default_factory=list)
    outline: list[dict] = field(default_factory=list)

    def symbols_named(self, name):
        return [symbol for symbol in self.symbols if symbol.name == name]


def uri_to_path(uri):
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return uri
    path = unquote(parsed.path)
    if os.name == "nt" and path.startswith("/") and re.match(r"^/[A-Za-z]:", path):
        path = path[1:]
    return path


def path_to_uri(path):
    absolute = os.path.abspath(path).replace("\\", "/")
    if os.name == "nt":
        return "file:///" + absolute
    return "file://" + absolute


def build_document_index(uri, source):
    path = uri_to_path(uri)
    index = DocumentIndex(uri=uri, path=path, source=source)

    try:
        normalized = source_tools.normalize_source(source)
        tokens = lexer.tokenize(normalized)
        index.program = parser.parse(tokens)
    except OPLError:
        return index

    collector = SymbolCollector(uri)
    collector.collect(index.program)
    index.symbols = collector.symbols
    index.outline = collector.outline
    return index


def read_file_index(path):
    with open(path, "r", encoding="utf-8-sig") as file:
        source = file.read()
    return build_document_index(path_to_uri(path), source)


def stdlib_symbols():
    symbols = []
    stdlib_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "opl", "stdlib")
    for module_name in stdlib_bindings.STDLIB_MODULES:
        uri = path_to_uri(os.path.join(stdlib_dir, module_name + ".opl"))
        symbols.append(
            Symbol(
                module_name,
                "module",
                1,
                1,
                uri,
                f"Standard library module: {module_name}",
            )
        )
        for function_name in stdlib_bindings.stdlib_function_names(module_name):
            symbols.append(
                Symbol(
                    function_name,
                    "function",
                    1,
                    1,
                    uri,
                    f"Stdlib function: {module_name}.{function_name}",
                    container=module_name,
                )
            )
    return symbols


def word_at(source, position):
    lines = source.splitlines()
    line_number = position.get("line", 0)
    character = position.get("character", 0)

    if line_number < 0 or line_number >= len(lines):
        return ""

    line = lines[line_number]
    if character > len(line):
        character = len(line)

    left = character
    while left > 0 and is_identifier_char(line[left - 1]):
        left -= 1

    right = character
    while right < len(line) and is_identifier_char(line[right]):
        right += 1

    return line[left:right]


def is_identifier_char(char):
    return char.isalnum() or char == "_"


class SymbolCollector:
    def __init__(self, uri):
        self.uri = uri
        self.symbols = []
        self.outline = []

    def collect(self, program):
        if not isinstance(program, Program):
            return
        for statement in program.statements:
            self.collect_statement(statement, top_level=True)

    def collect_statement(self, statement, top_level=False, container=""):
        if isinstance(statement, FunctionDeclaration):
            symbol = Symbol(
                statement.name,
                "function",
                statement.line,
                statement.column + 3,
                self.uri,
                f"Function: {statement.name}({', '.join(statement.parameters)})",
                statement.parameters,
                container,
            )
            self.symbols.append(symbol)
            if top_level:
                self.outline.append(self.document_symbol(symbol, KIND_FUNCTION))

            for index, parameter in enumerate(statement.parameters):
                self.symbols.append(
                    Symbol(
                        parameter,
                        "variable",
                        statement.line,
                        statement.column,
                        self.uri,
                        f"Parameter: {parameter}",
                        container=statement.name,
                    )
                )
            self.collect_block(statement.body, statement.name)

        elif isinstance(statement, ModelDeclaration):
            symbol = Symbol(
                statement.name,
                "model",
                statement.line,
                statement.column + 6,
                self.uri,
                f"Model: {statement.name}",
            )
            self.symbols.append(symbol)
            model_symbol = self.document_symbol(symbol, KIND_CLASS)

            for method in statement.methods:
                method_symbol = Symbol(
                    method.name,
                    "method",
                    method.line,
                    method.column + 3,
                    self.uri,
                    f"Method: {statement.name}.{method.name}({', '.join(method.parameters)})",
                    method.parameters,
                    statement.name,
                )
                self.symbols.append(method_symbol)
                model_symbol["children"].append(
                    self.document_symbol(method_symbol, KIND_METHOD)
                )
                for parameter in method.parameters:
                    self.symbols.append(
                        Symbol(
                            parameter,
                            "variable",
                            method.line,
                            method.column,
                            self.uri,
                            f"Parameter: {parameter}",
                            container=method.name,
                        )
                    )
                self.collect_block(method.body, method.name)

            if top_level:
                self.outline.append(model_symbol)

        elif isinstance(statement, LetStatement):
            symbol = Symbol(
                statement.name,
                "variable",
                statement.line,
                statement.column + 4,
                self.uri,
                f"Variable: {statement.name}",
                container=container,
            )
            self.symbols.append(symbol)
            if top_level:
                self.outline.append(self.document_symbol(symbol, KIND_VARIABLE))
            self.collect_expression(statement.value, container)

        elif isinstance(statement, ImportStatement):
            if stdlib_bindings.has_stdlib_module(statement.module_name):
                self.symbols.append(
                    Symbol(
                        statement.module_name,
                        "module",
                        statement.line,
                        statement.column + 7,
                        self.uri,
                        f"Standard library module: {statement.module_name}",
                    )
                )

        elif isinstance(statement, ForStatement):
            self.symbols.append(
                Symbol(
                    statement.name,
                    "variable",
                    statement.line,
                    statement.column + 4,
                    self.uri,
                    f"Loop variable: {statement.name}",
                    container=container,
                )
            )
            self.collect_expression(statement.iterable, container)
            self.collect_block(statement.body, container)

        elif isinstance(statement, (IfStatement, WhileStatement)):
            self.collect_expression(statement.condition, container)
            self.collect_block(statement.body, container)

        elif isinstance(statement, AssignmentStatement):
            self.collect_expression(statement.value, container)
        elif isinstance(statement, PropertyAssignment):
            self.collect_expression(statement.value, container)
        elif isinstance(statement, PrintStatement):
            self.collect_expression(statement.value, container)
        elif isinstance(statement, ReturnStatement):
            self.collect_expression(statement.value, container)
        elif isinstance(statement, ExpressionStatement):
            self.collect_expression(statement.expression, container)

    def collect_block(self, statements, container):
        for statement in statements:
            self.collect_statement(statement, container=container)

    def collect_expression(self, expression, container):
        if isinstance(expression, FunctionCall):
            for argument in expression.arguments:
                self.collect_expression(argument, container)
        elif isinstance(expression, MethodCall):
            for argument in expression.arguments:
                self.collect_expression(argument, container)

    def document_symbol(self, symbol, kind):
        return {
            "name": symbol.name,
            "detail": symbol.detail,
            "kind": kind,
            "range": symbol.range(),
            "selectionRange": symbol.range(),
            "children": [],
        }
