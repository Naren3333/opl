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
    Literal,
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


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        statements = []
        self.skip_newlines()
        while not self.check("EOF"):
            statements.append(self.statement())
            self.skip_newlines()
        return Program(statements)

    def statement(self):
        if self.match("LET"):
            return self.let_statement(self.previous())
        if self.match("PRINT"):
            return self.print_statement(self.previous())
        if self.match("FN"):
            return self.function_declaration(self.previous())
        if self.match("RETURN"):
            return self.return_statement(self.previous())
        if self.match("IMPORT"):
            return self.import_statement(self.previous())
        if self.match("MODEL"):
            return self.model_declaration(self.previous())
        if self.match("IF"):
            return self.if_statement(self.previous())
        if self.match("WHILE"):
            return self.while_statement(self.previous())
        if self.match("FOR"):
            return self.for_statement(self.previous())
        if self.check("IDENTIFIER") and self.check_next("="):
            return self.assignment_statement()

        return self.expression_statement()

    def let_statement(self, token):
        name = self.consume("IDENTIFIER", "Expected variable name after 'let'")
        self.consume("=", "Expected '=' after variable name")
        self.require_expression_after_equals()
        value = self.expression()
        self.end_statement()
        return LetStatement(name.value, value, token.line, token.column)

    def assignment_statement(self):
        name = self.consume("IDENTIFIER", "Expected variable name")
        self.consume("=", "Expected '=' after variable name")
        self.require_expression_after_equals()
        value = self.expression()
        self.end_statement()
        return AssignmentStatement(name.value, value, name.line, name.column)

    def print_statement(self, token):
        self.consume("(", "Expected '(' after 'print'")
        value = self.expression()
        self.consume(")", "Expected ')' after print value")
        self.end_statement()
        return PrintStatement(value, token.line, token.column)

    def function_declaration(self, token):
        name = self.consume("IDENTIFIER", "Expected function name after 'fn'")
        self.consume("(", "Expected '(' after function name")
        parameters = []
        if not self.check(")"):
            while True:
                parameter = self.consume("IDENTIFIER", "Expected parameter name")
                parameters.append(parameter.value)
                if not self.match(","):
                    break
        self.consume(")", "Expected ')' after parameters")
        body = self.block()
        return FunctionDeclaration(name.value, parameters, body, token.line, token.column)

    def return_statement(self, token):
        value = self.expression()
        self.end_statement()
        return ReturnStatement(value, token.line, token.column)

    def import_statement(self, token):
        name = self.consume("IDENTIFIER", "Expected module name after 'import'")
        self.end_statement()
        return ImportStatement(name.value, token.line, token.column)

    def model_declaration(self, token):
        name = self.consume("IDENTIFIER", "Expected model name after 'model'")
        self.consume("{", "Expected '{' before model body")
        methods = []
        self.skip_newlines()
        while not self.check("}") and not self.check("EOF"):
            if not self.match("FN"):
                raise self.error(self.peek(), "Expected method declaration")
            methods.append(self.function_declaration(self.previous()))
            self.skip_newlines()
        self.consume("}", "Expected '}' after model body")
        return ModelDeclaration(name.value, methods, token.line, token.column)

    def expression_statement(self):
        expression = self.expression()
        if self.match("="):
            if isinstance(expression, PropertyAccess):
                self.require_expression_after_equals()
                value = self.expression()
                self.end_statement()
                return PropertyAssignment(expression, value, expression.line, expression.column)
            if isinstance(expression, IndexAccess):
                self.require_expression_after_equals()
                value = self.expression()
                self.end_statement()
                return IndexAssignment(expression, value, expression.line, expression.column)
            else:
                raise self.error(expression, "Invalid assignment target")
        if not isinstance(expression, (FunctionCall, MethodCall)):
            raise self.error(expression, "Expected statement")
        self.end_statement()
        return ExpressionStatement(expression, expression.line, expression.column)

    def if_statement(self, token):
        condition = self.expression()
        body = self.block()
        return IfStatement(condition, body, token.line, token.column)

    def while_statement(self, token):
        condition = self.expression()
        body = self.block()
        return WhileStatement(condition, body, token.line, token.column)

    def for_statement(self, token):
        name = self.consume("IDENTIFIER", "Expected loop variable after 'for'")
        self.consume("IN", "Expected 'in' after loop variable")
        iterable = self.expression()
        body = self.block()
        return ForStatement(name.value, iterable, body, token.line, token.column)

    def block(self):
        self.consume("{", "Expected '{' before block")
        statements = []
        self.skip_newlines()
        while not self.check("}") and not self.check("EOF"):
            statements.append(self.statement())
            self.skip_newlines()
        self.consume("}", "Expected '}' after block")
        return statements

    def expression(self):
        return self.comparison()

    def comparison(self):
        expr = self.term()
        while self.match(">", "<", "==", "!="):
            operator = self.previous()
            right = self.term()
            expr = BinaryExpression(expr, operator.type, right, operator.line, operator.column)
        return expr

    def term(self):
        expr = self.factor()
        while self.match("+", "-"):
            operator = self.previous()
            right = self.factor()
            expr = BinaryExpression(expr, operator.type, right, operator.line, operator.column)
        return expr

    def factor(self):
        expr = self.unary()
        while self.match("*", "/"):
            operator = self.previous()
            right = self.unary()
            expr = BinaryExpression(expr, operator.type, right, operator.line, operator.column)
        return expr

    def unary(self):
        if self.match("-"):
            operator = self.previous()
            right = self.unary()
            return UnaryExpression(operator.type, right, operator.line, operator.column)
        return self.call()

    def call(self):
        expr = self.primary()

        while True:
            if self.match("("):
                paren = self.previous()
                arguments = self.arguments()
                expr = FunctionCall(expr, arguments, paren.line, paren.column)
            elif self.match("["):
                bracket = self.previous()
                index = self.expression()
                self.consume("]", "Expected ']' after index")
                expr = IndexAccess(expr, index, bracket.line, bracket.column)
            elif self.match("."):
                dot = self.previous()
                name = self.consume("IDENTIFIER", "Expected property name after '.'")
                if self.match("("):
                    arguments = self.arguments()
                    expr = MethodCall(expr, name.value, arguments, dot.line, dot.column)
                else:
                    expr = PropertyAccess(expr, name.value, dot.line, dot.column)
            else:
                break

        return expr

    def arguments(self):
        arguments = []
        if not self.check(")"):
            while True:
                arguments.append(self.expression())
                if not self.match(","):
                    break
        self.consume(")", "Expected ')' after arguments")
        return arguments

    def primary(self):
        if self.match("NUMBER", "STRING"):
            token = self.previous()
            return Literal(token.value, token.line, token.column)
        if self.match("TRUE"):
            token = self.previous()
            return Literal(True, token.line, token.column)
        if self.match("FALSE"):
            token = self.previous()
            return Literal(False, token.line, token.column)
        if self.match("IDENTIFIER"):
            token = self.previous()
            return Identifier(token.value, token.line, token.column)
        if self.match("("):
            expr = self.expression()
            self.consume(")", "Expected ')' after expression")
            return expr
        if self.match("["):
            return self.list_literal(self.previous())
        if self.match("{"):
            return self.map_literal(self.previous())

        token = self.peek()
        raise self.error(token, "Expected expression")

    def list_literal(self, token):
        elements = []
        self.skip_newlines()
        if not self.check("]"):
            while True:
                elements.append(self.expression())
                self.skip_newlines()
                if not self.match(","):
                    break
                self.skip_newlines()
        self.consume("]", "Expected ']' after list")
        return ListLiteral(elements, token.line, token.column)

    def map_literal(self, token):
        entries = []
        self.skip_newlines()
        if not self.check("}"):
            while True:
                key = self.expression()
                self.consume(":", "Expected ':' between map key and value")
                value = self.expression()
                entries.append((key, value))
                self.skip_newlines()
                if not self.match(","):
                    break
                self.skip_newlines()
        self.consume("}", "Expected '}' after map")
        return MapLiteral(entries, token.line, token.column)

    def match(self, *types):
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False

    def consume(self, type, message):
        if self.check(type):
            return self.advance()
        raise self.error(self.peek(), message)

    def check(self, type):
        return self.peek().type == type

    def check_next(self, type):
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type == type

    def advance(self):
        if not self.check("EOF"):
            self.current += 1
        return self.previous()

    def previous(self):
        return self.tokens[self.current - 1]

    def peek(self):
        return self.tokens[self.current]

    def skip_newlines(self):
        while self.match("NEWLINE"):
            pass

    def end_statement(self):
        if self.check("NEWLINE") or self.check("}") or self.check("EOF"):
            return
        raise self.error(self.peek(), "Expected end of statement")

    def require_expression_after_equals(self):
        if self.check("NEWLINE") or self.check("}") or self.check("EOF"):
            raise self.error(self.peek(), "Expected expression after '='")

    def error(self, token, message):
        return OPLError("OPL-001", "Syntax Error", message, token.line, token.column)


def parse(tokens):
    return Parser(tokens).parse()


