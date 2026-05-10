import os
import threading

from opl import lexer, parser, source as source_tools
from opl.errors import OPLError
from opl.vm import VirtualMachine, compile_program
from opl.vm.deserializer import load_chunk


class DAPDebugger:
    def __init__(self, session):
        self.session = session
        self.condition = threading.Condition()
        self.mode = "pause"
        self.line_breakpoints = set()
        self.instruction_breakpoints = set()
        self.step_out_depth = None
        self.vm = None
        self.current_frame = None
        self.current_instruction = None
        self.stopped = False
        self.last_line_break_key = None

    def set_breakpoints(self, lines):
        self.line_breakpoints = set(lines)

    def before_instruction(self, vm, frame, instruction):
        with self.condition:
            self.vm = vm
            self.current_frame = frame
            self.current_instruction = instruction

            if self.should_stop(frame, instruction):
                self.mode = "pause"
                self.stop("breakpoint")
            elif self.mode == "step":
                self.mode = "pause"
                self.stop("step")
            elif self.mode == "pause" and not self.stopped:
                self.stop("entry")

            while self.mode == "pause":
                self.condition.wait()

    def stop(self, reason):
        self.stopped = True
        self.session.send_stopped(reason)

    def should_stop(self, frame, instruction):
        ip = frame.ip
        if ip in self.instruction_breakpoints:
            return True
        if instruction.line in self.line_breakpoints:
            key = (id(frame.chunk), instruction.line)
            if key != self.last_line_break_key:
                self.last_line_break_key = key
                return True
        else:
            self.last_line_break_key = None
        if self.mode == "stepOut" and len(self.vm.frames) < self.step_out_depth:
            self.step_out_depth = None
            return True
        return False

    def continue_execution(self):
        with self.condition:
            self.stopped = False
            self.mode = "continue"
            self.condition.notify_all()

    def step(self):
        with self.condition:
            self.stopped = False
            self.mode = "step"
            self.condition.notify_all()

    def step_out(self):
        with self.condition:
            self.stopped = False
            self.step_out_depth = len(self.vm.frames) if self.vm else 1
            self.mode = "stepOut"
            self.condition.notify_all()

    def pause(self):
        with self.condition:
            self.mode = "pause"


class OPLDebugSession:
    def __init__(self, protocol):
        self.protocol = protocol
        self.program = None
        self.debugger = DAPDebugger(self)
        self.thread = None
        self.variable_refs = {}
        self.next_variable_ref = 1

    def launch(self, program):
        self.program = os.path.abspath(program)

    def start(self):
        self.thread = threading.Thread(target=self.run_program, daemon=True)
        self.thread.start()

    def run_program(self):
        try:
            chunk = self.load_program()
            base_dir = os.path.dirname(self.program)
            vm = VirtualMachine(
                base_dir=base_dir,
                debugger=self.debugger,
                output_func=lambda value: self.protocol.output(str(value) + "\n"),
            )
            vm.run(chunk)
            self.protocol.event("terminated", {})
        except OPLError as error:
            self.protocol.output(str(error) + "\n", category="stderr")
            self.protocol.event("terminated", {})
        except Exception as error:
            self.protocol.output(
                f"OPL-012 Debugger Error\nLine 1, Column 1\n\n{error}\n",
                category="stderr",
            )
            self.protocol.event("terminated", {})

    def load_program(self):
        if self.program.endswith(source_tools.BYTECODE_EXTENSION):
            return load_chunk(self.program)

        source_tools.validate_path(self.program)
        with open(self.program, "r", encoding="utf-8-sig") as file:
            source = source_tools.normalize_source(file.read())
        return compile_program(parser.parse(lexer.tokenize(source)))

    def set_breakpoints(self, lines):
        self.debugger.set_breakpoints(lines)
        return [
            {"verified": True, "line": line}
            for line in sorted(lines)
        ]

    def send_stopped(self, reason):
        self.protocol.event(
            "stopped",
            {
                "reason": reason,
                "threadId": 1,
                "allThreadsStopped": True,
            },
        )

    def continue_execution(self):
        self.debugger.continue_execution()

    def step(self):
        self.debugger.step()

    def step_out(self):
        self.debugger.step_out()

    def pause(self):
        self.debugger.pause()
        self.send_stopped("pause")

    def threads(self):
        return [{"id": 1, "name": "OPL VM"}]

    def stack_trace(self):
        frames = []
        vm = self.debugger.vm
        if not vm:
            return frames

        for index, frame in enumerate(reversed(vm.frames), start=1):
            instruction = self.current_instruction_for_frame(frame)
            name = "main" if frame.chunk.name == "<script>" else frame.chunk.name
            frames.append(
                {
                    "id": index,
                    "name": name,
                    "line": instruction.line if instruction else 1,
                    "column": instruction.column if instruction else 1,
                    "source": {
                        "name": os.path.basename(self.program or "main.opl"),
                        "path": self.program,
                    },
                }
            )
        return frames

    def current_instruction_for_frame(self, frame):
        index = min(frame.ip, len(frame.chunk.instructions) - 1)
        if index < 0:
            return None
        return frame.chunk.instructions[index]

    def scopes(self, frame_id):
        frame = self.frame_for_id(frame_id)
        if not frame:
            return []
        return [
            {
                "name": "Locals",
                "variablesReference": self.store_ref(frame.env),
                "expensive": False,
            },
            {
                "name": "Globals",
                "variablesReference": self.store_ref(self.debugger.vm.globals),
                "expensive": False,
            },
        ]

    def variables(self, variables_reference):
        value = self.variable_refs.get(variables_reference)
        if value is None:
            return []

        items = []
        if hasattr(value, "values"):
            raw_values = value.values
            if isinstance(raw_values, dict):
                iterable = raw_values.items()
            else:
                iterable = enumerate(raw_values)
            for name, item in iterable:
                items.append(self.variable_item(str(name), item))
        elif hasattr(value, "properties"):
            for name, item in value.properties.items():
                items.append(self.variable_item(name, item))
        elif isinstance(value, dict):
            for name, item in value.items():
                items.append(self.variable_item(str(name), item))
        return items

    def evaluate(self, expression):
        value = self.lookup(expression)
        return {
            "result": self.format_value(value) if value is not None else "undefined",
            "variablesReference": self.expand_ref(value),
        }

    def lookup(self, expression):
        parts = expression.split(".")
        if not parts:
            return None

        vm = self.debugger.vm
        if not vm:
            return None

        value = None
        for frame in reversed(vm.frames):
            value = frame.env.get(parts[0])
            if value is not vm.undefined:
                break
        else:
            value = vm.globals.get(parts[0])
            if value is vm.undefined:
                return None

        for part in parts[1:]:
            value = self.child_value(value, part)
            if value is None:
                return None
        return value

    def child_value(self, value, name):
        if hasattr(value, "properties") and name in value.properties:
            return value.properties[name]
        if hasattr(value, "values"):
            raw_values = value.values
            if isinstance(raw_values, dict) and name in raw_values:
                return raw_values[name]
        if hasattr(value, "closure"):
            result = value.closure.get(name)
            if result is not self.debugger.vm.undefined:
                return result
        return None

    def frame_for_id(self, frame_id):
        vm = self.debugger.vm
        if not vm:
            return None
        frames = list(reversed(vm.frames))
        index = frame_id - 1
        if index < 0 or index >= len(frames):
            return None
        return frames[index]

    def variable_item(self, name, value):
        return {
            "name": name,
            "value": self.format_value(value),
            "variablesReference": self.expand_ref(value),
        }

    def expand_ref(self, value):
        if hasattr(value, "values") or hasattr(value, "properties") or isinstance(value, dict):
            return self.store_ref(value)
        return 0

    def store_ref(self, value):
        reference = self.next_variable_ref
        self.next_variable_ref += 1
        self.variable_refs[reference] = value
        return reference

    def format_value(self, value):
        if hasattr(value, "values"):
            return repr(value)
        if hasattr(value, "properties"):
            return repr(value)
        return repr(value)

