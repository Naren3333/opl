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


UNDEFINED = object()


class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.values = {}

    def define(self, name, value):
        self.values[name] = value

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        return UNDEFINED

    def assign(self, name, value):
        if name in self.values:
            self.values[name] = value
            return True
        if self.parent:
            return self.parent.assign(name, value)
        return False


class ReturnSignal(Exception):
    def __init__(self, value, node):
        self.value = value
        self.node = node


class OPLFunction:
    def __init__(self, declaration, closure):
        self.declaration = declaration
        self.closure = closure

    def call(self, runtime, arguments, call_node):
        if len(arguments) != len(self.declaration.parameters):
            raise runtime.runtime_error(
                call_node,
                (
                    f"Expected {len(self.declaration.parameters)} arguments "
                    f"but got {len(arguments)}"
                ),
            )

        env = Environment(self.closure)
        for index, parameter in enumerate(self.declaration.parameters):
            env.define(parameter, arguments[index])

        try:
            runtime.eval_block(self.declaration.body, env)
        except ReturnSignal as signal:
            return signal.value

        return None


class BuiltinFunction:
    def __init__(self, name, arity, action):
        self.name = name
        self.arity = arity
        self.action = action

    def call(self, runtime, arguments, call_node):
        if len(arguments) != self.arity:
            raise runtime.runtime_error(
                call_node,
                f"Expected {self.arity} arguments but got {len(arguments)}",
            )
        return self.action(runtime, arguments, call_node)


class NativeModule:
    def __init__(self, name, functions):
        self.name = name
        self.functions = functions

    def get(self, name):
        return self.functions.get(name, UNDEFINED)


class OPLModel:
    def __init__(self, declaration, closure):
        self.declaration = declaration
        self.closure = closure
        self.methods = {}

        for method in declaration.methods:
            self.methods[method.name] = method

    def call(self, runtime, arguments, call_node):
        instance = OPLInstance(self)
        spawn = self.methods.get("spawn")

        if spawn:
            self.call_method(runtime, instance, "spawn", arguments, call_node)
        elif arguments:
            raise runtime.runtime_error(
                call_node,
                f"Expected 0 arguments but got {len(arguments)}",
            )

        return instance

    def call_method(self, runtime, instance, name, arguments, call_node):
        if name not in self.methods:
            raise runtime.runtime_error(call_node, f"Undefined method '{name}'")

        method = self.methods[name]

        if len(arguments) != len(method.parameters):
            raise runtime.runtime_error(
                call_node,
                f"Expected {len(method.parameters)} arguments but got {len(arguments)}",
            )

        env = Environment(self.closure)
        env.define("captain", instance)

        for index, parameter in enumerate(method.parameters):
            env.define(parameter, arguments[index])

        try:
            runtime.eval_block(method.body, env)
        except ReturnSignal as signal:
            return signal.value

        return None


class OPLInstance:
    def __init__(self, model):
        self.model = model
        self.properties = {}

    def get(self, name):
        return self.properties.get(name, UNDEFINED)

    def set(self, name, value):
        self.properties[name] = value


class Interpreter:
    def __init__(self, module_loader=None):
        self.module_loader = module_loader

    def eval(self, node, env):
        if isinstance(node, Program):
            return self.eval_program(node, env)
        if isinstance(node, LetStatement):
            return self.eval_let(node, env)
        if isinstance(node, AssignmentStatement):
            return self.eval_assignment(node, env)
        if isinstance(node, PropertyAssignment):
            return self.eval_property_assignment(node, env)
        if isinstance(node, IndexAssignment):
            return self.eval_index_assignment(node, env)
        if isinstance(node, ExpressionStatement):
            return self.eval(node.expression, env)
        if isinstance(node, FunctionDeclaration):
            return self.eval_function_declaration(node, env)
        if isinstance(node, ModelDeclaration):
            return self.eval_model_declaration(node, env)
        if isinstance(node, ReturnStatement):
            return self.eval_return(node, env)
        if isinstance(node, ImportStatement):
            return self.eval_import(node, env)
        if isinstance(node, PrintStatement):
            return self.eval_print(node, env)
        if isinstance(node, IfStatement):
            return self.eval_if(node, env)
        if isinstance(node, WhileStatement):
            return self.eval_while(node, env)
        if isinstance(node, ForStatement):
            return self.eval_for(node, env)
        if isinstance(node, Literal):
            return node.value
        if isinstance(node, ListLiteral):
            return self.eval_list_literal(node, env)
        if isinstance(node, MapLiteral):
            return self.eval_map_literal(node, env)
        if isinstance(node, Identifier):
            return self.eval_identifier(node, env)
        if isinstance(node, BinaryExpression):
            return self.eval_binary(node, env)
        if isinstance(node, UnaryExpression):
            return self.eval_unary(node, env)
        if isinstance(node, FunctionCall):
            return self.eval_function_call(node, env)
        if isinstance(node, IndexAccess):
            return self.eval_index_access(node, env)
        if isinstance(node, PropertyAccess):
            return self.eval_property_access(node, env)
        if isinstance(node, MethodCall):
            return self.eval_method_call(node, env)

        raise self.runtime_error(node, "Unknown AST node")

    def eval_program(self, node, env):
        try:
            for statement in node.statements:
                self.eval(statement, env)
        except ReturnSignal as signal:
            raise self.runtime_error(signal.node, "return used outside function")

    def eval_let(self, node, env):
        env.define(node.name, self.eval(node.value, env))

    def eval_assignment(self, node, env):
        value = self.eval(node.value, env)
        if not env.assign(node.name, value):
            raise self.runtime_error(node, f"Undefined variable '{node.name}'")

    def eval_print(self, node, env):
        print(self.eval(node.value, env))

    def eval_function_declaration(self, node, env):
        env.define(node.name, OPLFunction(node, env))

    def eval_model_declaration(self, node, env):
        env.define(node.name, OPLModel(node, env))

    def eval_return(self, node, env):
        raise ReturnSignal(self.eval(node.value, env), node)

    def eval_import(self, node, env):
        if not self.module_loader:
            raise self.runtime_error(node, "Imports are not available here")
        self.module_loader.import_module(node.module_name, env, node)

    def eval_if(self, node, env):
        if self.eval(node.condition, env):
            self.eval_block(node.body, Environment(env))

    def eval_while(self, node, env):
        while self.eval(node.condition, env):
            self.eval_block(node.body, Environment(env))

    def eval_for(self, node, env):
        iterable = self.eval(node.iterable, env)

        if isinstance(iterable, list):
            values = iterable
        elif isinstance(iterable, dict):
            values = list(iterable.keys())
        else:
            raise self.runtime_error(node, "for-in target must be a list or map")

        loop_env = Environment(env)
        for value in values:
            loop_env.define(node.name, value)
            self.eval_block(node.body, Environment(loop_env))

    def eval_block(self, statements, env):
        for statement in statements:
            self.eval(statement, env)

    def eval_identifier(self, node, env):
        value = env.get(node.name)
        if value is UNDEFINED:
            if node.name == "captain":
                raise self.runtime_error(node, "captain is only available inside methods")
            raise self.runtime_error(node, f"Undefined variable '{node.name}'")
        return value

    def eval_list_literal(self, node, env):
        values = []
        for element in node.elements:
            values.append(self.eval(element, env))
        return values

    def eval_map_literal(self, node, env):
        values = {}
        for key_expr, value_expr in node.entries:
            key = self.eval(key_expr, env)
            if not isinstance(key, (str, int)):
                raise self.runtime_error(node, "Map keys must be strings or numbers")
            values[key] = self.eval(value_expr, env)
        return values

    def eval_binary(self, node, env):
        left = self.eval(node.left, env)
        right = self.eval(node.right, env)

        try:
            if node.operator == "+":
                return left + right
            if node.operator == "-":
                return left - right
            if node.operator == "*":
                return left * right
            if node.operator == "/":
                return left / right
            if node.operator == ">":
                return left > right
            if node.operator == "<":
                return left < right
            if node.operator == "==":
                return left == right
            if node.operator == "!=":
                return left != right
        except TypeError:
            raise self.runtime_error(node, "Invalid operand types")
        except ZeroDivisionError:
            raise self.runtime_error(node, "Division by zero")

        raise self.runtime_error(node, f"Unknown operator '{node.operator}'")

    def eval_unary(self, node, env):
        value = self.eval(node.right, env)
        if node.operator == "-":
            if isinstance(value, int):
                return -value
            raise self.runtime_error(node, "Unary '-' expects a number")
        raise self.runtime_error(node, f"Unknown operator '{node.operator}'")

    def eval_function_call(self, node, env):
        if isinstance(node.callee, Identifier):
            callee = env.get(node.callee.name)
            if callee is UNDEFINED:
                raise self.runtime_error(
                    node,
                    f"Undefined function or model '{node.callee.name}'",
                )
        else:
            callee = self.eval(node.callee, env)

        if not isinstance(callee, (OPLFunction, OPLModel, BuiltinFunction)):
            raise self.runtime_error(node, "Can only call functions, models, or built-ins")

        arguments = []
        for argument in node.arguments:
            arguments.append(self.eval(argument, env))

        return callee.call(self, arguments, node)

    def eval_index_access(self, node, env):
        collection = self.eval(node.object_expr, env)
        index = self.eval(node.index, env)

        if isinstance(collection, list):
            if not isinstance(index, int):
                raise self.runtime_error(node, "List index must be a number")
            if index < 0 or index >= len(collection):
                raise self.runtime_error(node, "List index out of range")
            return collection[index]

        if isinstance(collection, dict):
            if not isinstance(index, (str, int)):
                raise self.runtime_error(node, "Map index must be a string or number")
            if index not in collection:
                raise self.runtime_error(node, f"Undefined map key '{index}'")
            return collection[index]

        raise self.runtime_error(node, "Can only index lists or maps")

    def eval_index_assignment(self, node, env):
        collection = self.eval(node.target.object_expr, env)
        index = self.eval(node.target.index, env)
        value = self.eval(node.value, env)

        if isinstance(collection, list):
            if not isinstance(index, int):
                raise self.runtime_error(node, "List index must be a number")
            if index < 0 or index >= len(collection):
                raise self.runtime_error(node, "List index out of range")
            collection[index] = value
            return

        if isinstance(collection, dict):
            if not isinstance(index, (str, int)):
                raise self.runtime_error(node, "Map index must be a string or number")
            collection[index] = value
            return

        raise self.runtime_error(node, "Can only assign indexes on lists or maps")

    def eval_property_access(self, node, env):
        instance = self.eval(node.object_expr, env)

        if isinstance(instance, NativeModule):
            value = instance.get(node.name)
            if value is UNDEFINED:
                raise self.runtime_error(node, f"Undefined stdlib member '{node.name}'")
            return value

        if not isinstance(instance, OPLInstance):
            raise self.runtime_error(node, "Invalid property access")

        value = instance.get(node.name)
        if value is UNDEFINED:
            raise self.runtime_error(node, f"Undefined property '{node.name}'")

        return value

    def eval_property_assignment(self, node, env):
        instance = self.eval(node.target.object_expr, env)

        if isinstance(instance, NativeModule):
            raise self.runtime_error(node, "Cannot assign stdlib module properties")

        if not isinstance(instance, OPLInstance):
            raise self.runtime_error(node, "Invalid property assignment")

        value = self.eval(node.value, env)
        instance.set(node.target.name, value)

    def eval_method_call(self, node, env):
        instance = self.eval(node.object_expr, env)

        if isinstance(instance, NativeModule):
            function = instance.get(node.name)
            if function is UNDEFINED:
                raise self.runtime_error(node, f"Undefined stdlib function '{node.name}'")
            arguments = []
            for argument in node.arguments:
                arguments.append(self.eval(argument, env))
            return function.call(self, arguments, node)

        if not isinstance(instance, OPLInstance):
            raise self.runtime_error(node, "Invalid method call")

        arguments = []
        for argument in node.arguments:
            arguments.append(self.eval(argument, env))

        return instance.model.call_method(self, instance, node.name, arguments, node)

    def runtime_error(self, node, message):
        return OPLError(
            "OPL-003",
            "Runtime Error",
            message,
            node.line,
            node.column,
            type(node).__name__,
        )


def run(program):
    Interpreter().eval(program, create_global_env())


def create_global_env():
    env = Environment()
    env.define("len", BuiltinFunction("len", 1, builtin_len))
    env.define("append", BuiltinFunction("append", 2, builtin_append))
    env.define("keys", BuiltinFunction("keys", 1, builtin_keys))
    return env


def builtin_len(runtime, arguments, node):
    value = arguments[0]
    if isinstance(value, (list, dict, str)):
        return len(value)
    raise runtime.runtime_error(node, "len expects a list, map, or string")


def builtin_append(runtime, arguments, node):
    target = arguments[0]
    if not isinstance(target, list):
        raise runtime.runtime_error(node, "append expects a list")
    target.append(arguments[1])
    return None


def builtin_keys(runtime, arguments, node):
    target = arguments[0]
    if not isinstance(target, dict):
        raise runtime.runtime_error(node, "keys expects a map")
    return list(target.keys())


