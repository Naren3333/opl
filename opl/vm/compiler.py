from opl.ast import (
    AssignmentStatement,
    BinaryExpression,
    ExpressionStatement,
    ForStatement,
    FunctionCall,
    FunctionDeclaration,
    Identifier,
    IfStatement,
    ImportStatement,
    IndexAccess,
    IndexAssignment,
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
from opl.vm.chunk import Chunk
from opl.vm.instructions import (
    ADD,
    BUILD_LIST,
    BUILD_MAP,
    BUILD_MODEL,
    CALL,
    DEFINE_NAME,
    DIV,
    EQ,
    GET_INDEX,
    GET_ITER,
    GET_PROPERTY,
    GT,
    IMPORT_NAME,
    ITER_NEXT,
    JUMP,
    JUMP_IF_FALSE,
    LOAD_NAME,
    MAKE_CLOSURE,
    METHOD_CALL,
    LT,
    MUL,
    NE,
    NEG,
    POP,
    PRINT,
    PUSH_CONST,
    RETURN,
    SET_INDEX,
    SET_PROPERTY,
    STORE_NAME,
    SUB,
)


class CompiledFunction:
    def __init__(self, name, parameters, chunk, line, column):
        self.name = name
        self.parameters = parameters
        self.chunk = chunk
        self.line = line
        self.column = column

    def __repr__(self):
        return f"<fn {self.name}>"


class Compiler:
    def __init__(self, name="<script>"):
        self.chunk = Chunk(name)
        self.loop_index = 0

    def compile(self, program):
        self.statement_list(program.statements)
        self.emit(PUSH_CONST, None, program)
        self.emit(RETURN, None, program)
        return self.chunk

    def statement_list(self, statements):
        for statement in statements:
            self.statement(statement)

    def statement(self, node):
        if isinstance(node, LetStatement):
            self.expression(node.value)
            self.emit(DEFINE_NAME, node.name, node)
        elif isinstance(node, AssignmentStatement):
            self.expression(node.value)
            self.emit(STORE_NAME, node.name, node)
        elif isinstance(node, IndexAssignment):
            self.expression(node.target.object_expr)
            self.expression(node.target.index)
            self.expression(node.value)
            self.emit(SET_INDEX, None, node)
        elif isinstance(node, PropertyAssignment):
            self.expression(node.target.object_expr)
            self.expression(node.value)
            self.emit(SET_PROPERTY, node.target.name, node)
        elif isinstance(node, PrintStatement):
            self.expression(node.value)
            self.emit(PRINT, None, node)
        elif isinstance(node, ExpressionStatement):
            self.expression(node.expression)
            self.emit(POP, None, node)
        elif isinstance(node, FunctionDeclaration):
            function = self.compile_function(node)
            self.emit(MAKE_CLOSURE, function, node)
            self.emit(DEFINE_NAME, node.name, node)
        elif isinstance(node, ModelDeclaration):
            methods = []
            for method in node.methods:
                methods.append(self.compile_function(method))
            self.emit(BUILD_MODEL, (node.name, methods), node)
            self.emit(DEFINE_NAME, node.name, node)
        elif isinstance(node, ReturnStatement):
            self.expression(node.value)
            self.emit(RETURN, None, node)
        elif isinstance(node, ImportStatement):
            self.emit(IMPORT_NAME, node.module_name, node)
        elif isinstance(node, IfStatement):
            self.if_statement(node)
        elif isinstance(node, WhileStatement):
            self.while_statement(node)
        elif isinstance(node, ForStatement):
            self.for_statement(node)
        else:
            self.unsupported(node)

    def if_statement(self, node):
        self.expression(node.condition)
        jump_to_end = self.emit(JUMP_IF_FALSE, None, node)
        self.statement_list(node.body)
        self.chunk.patch(jump_to_end, self.chunk.current_offset())

    def while_statement(self, node):
        loop_start = self.chunk.current_offset()
        self.expression(node.condition)
        jump_to_end = self.emit(JUMP_IF_FALSE, None, node)
        self.statement_list(node.body)
        self.emit(JUMP, loop_start, node)
        self.chunk.patch(jump_to_end, self.chunk.current_offset())

    def for_statement(self, node):
        iterator_name = f"__iter_{self.loop_index}"
        self.loop_index += 1

        self.expression(node.iterable)
        self.emit(GET_ITER, None, node)
        self.emit(DEFINE_NAME, iterator_name, node)

        loop_start = self.chunk.current_offset()
        self.emit(LOAD_NAME, iterator_name, node)
        jump_to_end = self.emit(ITER_NEXT, None, node)
        self.emit(DEFINE_NAME, node.name, node)
        self.statement_list(node.body)
        self.emit(JUMP, loop_start, node)
        self.chunk.patch(jump_to_end, self.chunk.current_offset())

    def compile_function(self, node):
        compiler = Compiler(node.name)
        compiler.statement_list(node.body)
        compiler.emit(PUSH_CONST, None, node)
        compiler.emit(RETURN, None, node)
        return CompiledFunction(
            node.name,
            node.parameters,
            compiler.chunk,
            node.line,
            node.column,
        )

    def expression(self, node):
        if isinstance(node, Literal):
            self.emit(PUSH_CONST, node.value, node)
        elif isinstance(node, Identifier):
            self.emit(LOAD_NAME, node.name, node)
        elif isinstance(node, UnaryExpression):
            self.expression(node.right)
            if node.operator == "-":
                self.emit(NEG, None, node)
            else:
                self.unsupported(node)
        elif isinstance(node, BinaryExpression):
            self.expression(node.left)
            self.expression(node.right)
            self.binary_operator(node)
        elif isinstance(node, FunctionCall):
            self.function_call(node)
        elif isinstance(node, ListLiteral):
            for element in node.elements:
                self.expression(element)
            self.emit(BUILD_LIST, len(node.elements), node)
        elif isinstance(node, MapLiteral):
            for key, value in node.entries:
                self.expression(key)
                self.expression(value)
            self.emit(BUILD_MAP, len(node.entries), node)
        elif isinstance(node, IndexAccess):
            self.expression(node.object_expr)
            self.expression(node.index)
            self.emit(GET_INDEX, None, node)
        elif isinstance(node, PropertyAccess):
            self.expression(node.object_expr)
            self.emit(GET_PROPERTY, node.name, node)
        elif isinstance(node, MethodCall):
            self.method_call(node)
        else:
            self.unsupported(node)

    def binary_operator(self, node):
        opcodes = {
            "+": ADD,
            "-": SUB,
            "*": MUL,
            "/": DIV,
            ">": GT,
            "<": LT,
            "==": EQ,
            "!=": NE,
        }
        if node.operator not in opcodes:
            self.unsupported(node)
        self.emit(opcodes[node.operator], None, node)

    def function_call(self, node):
        self.expression(node.callee)
        for argument in node.arguments:
            self.expression(argument)
        self.emit(CALL, len(node.arguments), node)

    def method_call(self, node):
        self.expression(node.object_expr)
        for argument in node.arguments:
            self.expression(argument)
        self.emit(METHOD_CALL, (node.name, len(node.arguments)), node)

    def emit(self, opcode, operand=None, node=None):
        line = getattr(node, "line", 1)
        column = getattr(node, "column", 1)
        return self.chunk.emit(opcode, operand, line, column)

    def unsupported(self, node):
        raise OPLError(
            "OPL-009",
            "VM Compile Error",
            f"VM backend does not support {type(node).__name__} yet",
            getattr(node, "line", 1),
            getattr(node, "column", 1),
            type(node).__name__,
        )


def compile_program(program):
    if not isinstance(program, Program):
        raise OPLError("OPL-009", "VM Compile Error", "Expected program AST", 1, 1)
    return Compiler().compile(program)
