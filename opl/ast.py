class Program:
    def __init__(self, statements):
        self.statements = statements
        self.line = 1
        self.column = 1


class LetStatement:
    def __init__(self, name, value, line, column):
        self.name = name
        self.value = value
        self.line = line
        self.column = column


class AssignmentStatement:
    def __init__(self, name, value, line, column):
        self.name = name
        self.value = value
        self.line = line
        self.column = column


class PrintStatement:
    def __init__(self, value, line, column):
        self.value = value
        self.line = line
        self.column = column


class ExpressionStatement:
    def __init__(self, expression, line, column):
        self.expression = expression
        self.line = line
        self.column = column


class FunctionDeclaration:
    def __init__(self, name, parameters, body, line, column):
        self.name = name
        self.parameters = parameters
        self.body = body
        self.line = line
        self.column = column


class ReturnStatement:
    def __init__(self, value, line, column):
        self.value = value
        self.line = line
        self.column = column


class ImportStatement:
    def __init__(self, module_name, line, column):
        self.module_name = module_name
        self.line = line
        self.column = column


class ModelDeclaration:
    def __init__(self, name, methods, line, column):
        self.name = name
        self.methods = methods
        self.line = line
        self.column = column


class PropertyAssignment:
    def __init__(self, target, value, line, column):
        self.target = target
        self.value = value
        self.line = line
        self.column = column


class IndexAssignment:
    def __init__(self, target, value, line, column):
        self.target = target
        self.value = value
        self.line = line
        self.column = column


class IfStatement:
    def __init__(self, condition, body, line, column):
        self.condition = condition
        self.body = body
        self.line = line
        self.column = column


class WhileStatement:
    def __init__(self, condition, body, line, column):
        self.condition = condition
        self.body = body
        self.line = line
        self.column = column


class ForStatement:
    def __init__(self, name, iterable, body, line, column):
        self.name = name
        self.iterable = iterable
        self.body = body
        self.line = line
        self.column = column


class BinaryExpression:
    def __init__(self, left, operator, right, line, column):
        self.left = left
        self.operator = operator
        self.right = right
        self.line = line
        self.column = column


class UnaryExpression:
    def __init__(self, operator, right, line, column):
        self.operator = operator
        self.right = right
        self.line = line
        self.column = column


class Literal:
    def __init__(self, value, line, column):
        self.value = value
        self.line = line
        self.column = column


class Identifier:
    def __init__(self, name, line, column):
        self.name = name
        self.line = line
        self.column = column


class FunctionCall:
    def __init__(self, callee, arguments, line, column):
        self.callee = callee
        self.arguments = arguments
        self.line = line
        self.column = column


class ListLiteral:
    def __init__(self, elements, line, column):
        self.elements = elements
        self.line = line
        self.column = column


class MapLiteral:
    def __init__(self, entries, line, column):
        self.entries = entries
        self.line = line
        self.column = column


class IndexAccess:
    def __init__(self, object_expr, index, line, column):
        self.object_expr = object_expr
        self.index = index
        self.line = line
        self.column = column


class PropertyAccess:
    def __init__(self, object_expr, name, line, column):
        self.object_expr = object_expr
        self.name = name
        self.line = line
        self.column = column


class MethodCall:
    def __init__(self, object_expr, name, arguments, line, column):
        self.object_expr = object_expr
        self.name = name
        self.arguments = arguments
        self.line = line
        self.column = column


