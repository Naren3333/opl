import os

from opl import lexer, parser, source as source_tools, stdlib_bindings
from opl.errors import OPLError
from opl.interpreter import BuiltinFunction, NativeModule, UNDEFINED as INTERPRETER_UNDEFINED
from opl.vm.gc import GarbageCollector, ManagedObject
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


UNDEFINED = object()


class VMEnvironment(ManagedObject):
    def __init__(self, parent=None):
        super().__init__()
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

    def children(self):
        children = []
        if self.parent:
            children.append(self.parent)
        children.extend(self.values.values())
        return children

    def gc_name(self):
        return "environment"


class VMFunction(ManagedObject):
    def __init__(self, compiled, closure):
        super().__init__()
        self.name = compiled.name
        self.parameters = compiled.parameters
        self.chunk = compiled.chunk
        self.closure = closure

    def __repr__(self):
        return f"<fn {self.name}>"

    def children(self):
        return [self.closure]

    def gc_name(self):
        return f"closure <fn {self.name}>"


class VMList(ManagedObject):
    def __init__(self, values):
        super().__init__()
        self.values = values

    def children(self):
        return self.values

    def gc_name(self):
        return "list"

    def __repr__(self):
        return repr(self.values)


class VMMap(ManagedObject):
    def __init__(self, values):
        super().__init__()
        self.values = values

    def children(self):
        children = []
        for key, value in self.values.items():
            children.append(key)
            children.append(value)
        return children

    def gc_name(self):
        return "map"

    def __repr__(self):
        return repr(self.values)


class VMIterator(ManagedObject):
    def __init__(self, values):
        super().__init__()
        self.values = values
        self.index = 0

    def children(self):
        return self.values

    def gc_name(self):
        return "iterator"

    def next(self):
        if self.index >= len(self.values):
            return UNDEFINED
        value = self.values[self.index]
        self.index += 1
        return value


class VMModel(ManagedObject):
    def __init__(self, name, methods, closure):
        super().__init__()
        self.name = name
        self.methods = {}
        for method in methods:
            self.methods[method.name] = method
        self.closure = closure

    def children(self):
        return [self.closure]

    def gc_name(self):
        return f"model {self.name}"

    def __repr__(self):
        return f"<model {self.name}>"


class VMInstance(ManagedObject):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.properties = {}

    def children(self):
        return [self.model] + list(self.properties.values())

    def gc_name(self):
        return f"instance {self.model.name}"

    def __repr__(self):
        return f"<{self.model.name} instance>"


NO_RETURN_OVERRIDE = object()


class CallFrame:
    def __init__(self, chunk, env, return_override=NO_RETURN_OVERRIDE):
        self.chunk = chunk
        self.env = env
        self.ip = 0
        self.return_override = return_override


class VirtualMachine:
    def __init__(
        self,
        debug_gc=False,
        gc_threshold=64,
        base_dir=None,
        debugger=None,
        output_func=print,
    ):
        self.stack = []
        self.frames = []
        self.debugger = debugger
        self.output = output_func
        self.undefined = UNDEFINED
        self.gc = GarbageCollector(threshold=gc_threshold, debug=debug_gc)
        self.globals = self.allocate_environment()
        self.base_dir = os.path.abspath(base_dir or os.getcwd())
        self.module_cache = {}
        self.module_loader = VMModuleContext(self.base_dir)
        self.define_builtins()

    def run(self, chunk):
        self.stack = []
        self.frames = [CallFrame(chunk, self.globals)]
        result = self.execute()
        self.collect_garbage()
        return result

    def execute(self):
        while self.frames:
            frame = self.frames[-1]

            if frame.ip >= len(frame.chunk.instructions):
                self.frames.pop()
                continue

            instruction = frame.chunk.instructions[frame.ip]
            if self.debugger:
                self.debugger.before_instruction(self, frame, instruction)
            frame.ip += 1
            opcode = instruction.opcode

            if opcode == PUSH_CONST:
                self.push(instruction.operand)
            elif opcode == MAKE_CLOSURE:
                self.push(self.allocate_function(instruction.operand, frame.env))
                self.maybe_collect_garbage()
            elif opcode == BUILD_LIST:
                self.build_list(instruction)
            elif opcode == BUILD_MAP:
                self.build_map(instruction)
            elif opcode == BUILD_MODEL:
                name, methods = instruction.operand
                self.push(self.allocate_model(name, methods, frame.env))
                self.maybe_collect_garbage()
            elif opcode == IMPORT_NAME:
                self.import_module(instruction.operand, frame.env, instruction)
            elif opcode == GET_INDEX:
                self.get_index(instruction)
            elif opcode == SET_INDEX:
                self.set_index(instruction)
            elif opcode == GET_PROPERTY:
                self.get_property(instruction)
            elif opcode == SET_PROPERTY:
                self.set_property(instruction)
            elif opcode == METHOD_CALL:
                self.method_call(instruction)
            elif opcode == GET_ITER:
                self.get_iter(instruction)
            elif opcode == ITER_NEXT:
                self.iter_next(instruction, frame)
            elif opcode == LOAD_NAME:
                value = frame.env.get(instruction.operand)
                if value is UNDEFINED:
                    self.error(instruction, f"Undefined variable '{instruction.operand}'")
                self.push(value)
            elif opcode == DEFINE_NAME:
                frame.env.define(instruction.operand, self.pop())
            elif opcode == STORE_NAME:
                value = self.pop()
                if not frame.env.assign(instruction.operand, value):
                    self.error(instruction, f"Undefined variable '{instruction.operand}'")
            elif opcode == ADD:
                self.binary(instruction, lambda left, right: left + right)
            elif opcode == SUB:
                self.binary(instruction, lambda left, right: left - right)
            elif opcode == MUL:
                self.binary(instruction, lambda left, right: left * right)
            elif opcode == DIV:
                self.binary(instruction, lambda left, right: left / right)
            elif opcode == NEG:
                value = self.pop()
                if not isinstance(value, int):
                    self.error(instruction, "Unary '-' expects a number")
                self.push(-value)
            elif opcode == GT:
                self.binary(instruction, lambda left, right: left > right)
            elif opcode == LT:
                self.binary(instruction, lambda left, right: left < right)
            elif opcode == EQ:
                self.binary(instruction, lambda left, right: left == right)
            elif opcode == NE:
                self.binary(instruction, lambda left, right: left != right)
            elif opcode == JUMP:
                frame.ip = instruction.operand
            elif opcode == JUMP_IF_FALSE:
                condition = self.pop()
                if not condition:
                    frame.ip = instruction.operand
            elif opcode == CALL:
                arity = instruction.operand
                arguments = self.pop_arguments(arity)
                callee = self.pop()
                self.call_value(callee, arguments, instruction)
            elif opcode == RETURN:
                value = self.pop()
                finished_frame = self.frames.pop()
                if finished_frame.return_override is not NO_RETURN_OVERRIDE:
                    value = finished_frame.return_override
                if not self.frames:
                    return value
                self.push(value)
            elif opcode == PRINT:
                self.output(self.unwrap(self.pop()))
            elif opcode == POP:
                self.pop()
            else:
                self.error(instruction, f"Unknown instruction '{opcode}'")

        return None

    def call(self, instruction):
        arity = instruction.operand
        arguments = self.pop_arguments(arity)
        callee = self.pop()
        self.call_value(callee, arguments, instruction)

    def call_value(self, callee, arguments, instruction):
        if not isinstance(callee, VMFunction):
            if isinstance(callee, VMModel):
                self.call_model(callee, arguments, instruction)
                return
            if isinstance(callee, BuiltinFunction):
                self.push(callee.call(self, arguments, instruction))
                return
            self.error(instruction, "Can only call functions, models, or built-ins")

        if len(arguments) != len(callee.parameters):
            self.error(
                instruction,
                f"Expected {len(callee.parameters)} arguments but got {len(arguments)}",
            )

        env = self.allocate_environment(callee.closure)
        for index, parameter in enumerate(callee.parameters):
            env.define(parameter, arguments[index])

        self.frames.append(CallFrame(callee.chunk, env))
        self.maybe_collect_garbage()

    def call_model(self, model, arguments, instruction):
        instance = self.allocate_instance(model)
        spawn = model.methods.get("spawn")

        if spawn:
            self.call_method_on_instance(
                instance,
                "spawn",
                arguments,
                instruction,
                return_override=instance,
            )
        elif arguments:
            self.error(instruction, f"Expected 0 arguments but got {len(arguments)}")
        else:
            self.push(instance)

    def call_method_on_instance(
        self,
        instance,
        name,
        arguments,
        instruction,
        return_override=NO_RETURN_OVERRIDE,
    ):
        method = instance.model.methods.get(name)
        if method is None:
            self.error(instruction, f"Undefined method '{name}'")
        if len(arguments) != len(method.parameters):
            self.error(
                instruction,
                f"Expected {len(method.parameters)} arguments but got {len(arguments)}",
            )

        env = self.allocate_environment(instance.model.closure)
        env.define("captain", instance)
        for index, parameter in enumerate(method.parameters):
            env.define(parameter, arguments[index])
        self.frames.append(CallFrame(method.chunk, env, return_override))
        self.maybe_collect_garbage()

    def pop_arguments(self, arity):
        arguments = []
        for _ in range(arity):
            arguments.append(self.pop())
        arguments.reverse()
        return arguments

    def build_list(self, instruction):
        values = self.pop_arguments(instruction.operand)
        self.push(self.allocate_list(values))
        self.maybe_collect_garbage()

    def build_map(self, instruction):
        values = {}
        pairs = self.pop_arguments(instruction.operand * 2)
        for index in range(0, len(pairs), 2):
            key = pairs[index]
            value = pairs[index + 1]
            if not isinstance(key, (str, int)):
                self.error(instruction, "Map keys must be strings or numbers")
            values[key] = value
        self.push(self.allocate_map(values))
        self.maybe_collect_garbage()

    def get_index(self, instruction):
        index = self.pop()
        collection = self.pop()
        if isinstance(collection, VMList):
            if not isinstance(index, int):
                self.error(instruction, "List index must be a number")
            if index < 0 or index >= len(collection.values):
                self.error(instruction, "List index out of range")
            self.push(collection.values[index])
            return
        if isinstance(collection, VMMap):
            if not isinstance(index, (str, int)):
                self.error(instruction, "Map index must be a string or number")
            if index not in collection.values:
                self.error(instruction, f"Undefined map key '{index}'")
            self.push(collection.values[index])
            return
        self.error(instruction, "Can only index lists or maps")

    def set_index(self, instruction):
        value = self.pop()
        index = self.pop()
        collection = self.pop()
        if isinstance(collection, VMList):
            if not isinstance(index, int):
                self.error(instruction, "List index must be a number")
            if index < 0 or index >= len(collection.values):
                self.error(instruction, "List index out of range")
            collection.values[index] = value
            return
        if isinstance(collection, VMMap):
            if not isinstance(index, (str, int)):
                self.error(instruction, "Map index must be a string or number")
            collection.values[index] = value
            return
        self.error(instruction, "Can only assign indexes on lists or maps")

    def get_property(self, instruction):
        name = instruction.operand
        target = self.pop()
        if isinstance(target, VMInstance):
            if name not in target.properties:
                self.error(instruction, f"Undefined property '{name}'")
            self.push(target.properties[name])
            return
        if isinstance(target, NativeModule):
            value = target.get(name)
            if value is INTERPRETER_UNDEFINED:
                self.error(instruction, f"Undefined stdlib member '{name}'")
            self.push(value)
            return
        self.error(instruction, "Invalid property access")

    def set_property(self, instruction):
        value = self.pop()
        target = self.pop()
        if not isinstance(target, VMInstance):
            self.error(instruction, "Invalid property assignment")
        target.properties[instruction.operand] = value

    def method_call(self, instruction):
        name, arity = instruction.operand
        arguments = self.pop_arguments(arity)
        target = self.pop()
        if isinstance(target, VMInstance):
            self.call_method_on_instance(target, name, arguments, instruction)
            return
        if isinstance(target, NativeModule):
            function = target.get(name)
            if function is INTERPRETER_UNDEFINED:
                self.error(instruction, f"Undefined stdlib function '{name}'")
            self.push(function.call(self, arguments, instruction))
            return
        self.error(instruction, "Invalid method call")

    def get_iter(self, instruction):
        target = self.pop()
        if isinstance(target, VMList):
            values = list(target.values)
        elif isinstance(target, VMMap):
            values = list(target.values.keys())
        else:
            self.error(instruction, "for-in target must be a list or map")
        self.push(self.allocate_iterator(values))
        self.maybe_collect_garbage()

    def iter_next(self, instruction, frame):
        iterator = self.pop()
        if not isinstance(iterator, VMIterator):
            self.error(instruction, "Invalid iterator")
        value = iterator.next()
        if value is UNDEFINED:
            frame.ip = instruction.operand
            return
        self.push(value)

    def import_module(self, module_name, env, instruction):
        if stdlib_bindings.has_stdlib_module(module_name):
            env.define(module_name, stdlib_bindings.create_stdlib_module(module_name))
            return

        path = os.path.abspath(os.path.join(self.base_dir, module_name + ".opl"))
        if not os.path.exists(path):
            self.error(instruction, f"Module '{module_name}' not found")

        if path not in self.module_cache:
            with open(path, "r", encoding="utf-8-sig") as file:
                source = source_tools.normalize_source(file.read())
            program = parser.parse(lexer.tokenize(source))
            from opl.vm.compiler import compile_program

            module_vm = VirtualMachine(
                debug_gc=self.gc.debug,
                gc_threshold=self.gc.threshold,
                base_dir=os.path.dirname(path),
                debugger=self.debugger,
                output_func=self.output,
            )
            module_vm.run(compile_program(program))
            self.module_cache[path] = dict(module_vm.globals.values)

        for name, value in self.module_cache[path].items():
            if not name.startswith("__"):
                env.define(name, value)

    def binary(self, instruction, operation):
        right = self.pop()
        left = self.pop()
        left = self.unwrap(left)
        right = self.unwrap(right)
        try:
            self.push(operation(left, right))
        except TypeError:
            self.error(instruction, "Invalid operand types")
        except ZeroDivisionError:
            self.error(instruction, "Division by zero")

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        if not self.stack:
            self.error(None, "VM stack underflow")
        return self.stack.pop()

    def allocate_environment(self, parent=None):
        return self.gc.track(VMEnvironment(parent))

    def allocate_function(self, compiled, closure):
        return self.gc.track(VMFunction(compiled, closure))

    def allocate_list(self, values):
        return self.gc.track(VMList(values))

    def allocate_map(self, values):
        return self.gc.track(VMMap(values))

    def allocate_iterator(self, values):
        return self.gc.track(VMIterator(values))

    def allocate_model(self, name, methods, closure):
        return self.gc.track(VMModel(name, methods, closure))

    def allocate_instance(self, model):
        return self.gc.track(VMInstance(model))

    def define_builtins(self):
        self.globals.define("len", BuiltinFunction("len", 1, vm_builtin_len))
        self.globals.define("append", BuiltinFunction("append", 2, vm_builtin_append))
        self.globals.define("keys", BuiltinFunction("keys", 1, vm_builtin_keys))

    def maybe_collect_garbage(self):
        if self.gc.should_collect():
            self.collect_garbage()

    def collect_garbage(self):
        self.gc.collect(self.roots())

    def roots(self):
        roots = list(self.stack)
        roots.append(self.globals)
        for frame in self.frames:
            roots.append(frame.env)
        return roots

    def unwrap(self, value):
        if isinstance(value, VMList):
            return value.values
        if isinstance(value, VMMap):
            return value.values
        return value

    def runtime_error(self, node, message):
        return self.error(node, message)

    def error(self, instruction, message):
        line = getattr(instruction, "line", 1)
        column = getattr(instruction, "column", 1)
        raise OPLError("OPL-010", "VM Runtime Error", message, line, column)


class VMModuleContext:
    def __init__(self, base_dir):
        self.base_dir = base_dir


def vm_builtin_len(runtime, arguments, node):
    value = arguments[0]
    if isinstance(value, VMList):
        return len(value.values)
    if isinstance(value, VMMap):
        return len(value.values)
    if isinstance(value, str):
        return len(value)
    raise runtime.runtime_error(node, "len expects a list, map, or string")


def vm_builtin_append(runtime, arguments, node):
    target = arguments[0]
    if not isinstance(target, VMList):
        raise runtime.runtime_error(node, "append expects a list")
    target.values.append(arguments[1])
    return None


def vm_builtin_keys(runtime, arguments, node):
    target = arguments[0]
    if not isinstance(target, VMMap):
        raise runtime.runtime_error(node, "keys expects a map")
    return runtime.allocate_list(list(target.values.keys()))
