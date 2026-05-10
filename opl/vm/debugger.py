from opl.errors import OPLError


class VMDebugger:
    def __init__(self, input_func=input, output_func=print):
        self.input = input_func
        self.output = output_func
        self.paused = True
        self.instruction_breakpoints = set()
        self.line_breakpoints = set()

    def before_instruction(self, vm, frame, instruction):
        ip = frame.ip
        hit_breakpoint = self.is_breakpoint(ip, instruction)

        if hit_breakpoint:
            self.output(f"[debug] Hit breakpoint at IP {ip}")

        if not self.paused and not hit_breakpoint:
            return

        self.print_trace(vm, frame, instruction)
        self.command_loop(vm, frame, instruction)

    def is_breakpoint(self, ip, instruction):
        return (
            ip in self.instruction_breakpoints
            or getattr(instruction, "line", None) in self.line_breakpoints
        )

    def print_trace(self, vm, frame, instruction):
        self.output(f"IP: {frame.ip:04d}")
        operand = ""
        if instruction.operand is not None:
            operand = f" {instruction.operand}"
        self.output(f"EXEC: {instruction.opcode}{operand}")
        self.output(f"SOURCE: line {instruction.line}, column {instruction.column}")
        self.output(f"STACK: {self.format_value(vm.stack)}")

    def command_loop(self, vm, frame, instruction):
        while True:
            try:
                command = self.input("(opldbg) ").strip()
            except EOFError:
                command = "continue"

            if command in ("", "step", "s"):
                self.paused = True
                return
            if command in ("continue", "c"):
                self.paused = False
                return
            if command in ("pause", "p"):
                self.paused = True
                self.output("Paused.")
                continue
            if command in ("stack", "bt", "backtrace"):
                self.print_call_stack(vm)
                continue
            if command in ("locals", "frames"):
                self.print_locals(vm)
                continue
            if command.startswith("inspect "):
                self.inspect(vm, command[len("inspect "):].strip())
                continue
            if command.startswith("break "):
                self.add_breakpoint(command[len("break "):].strip(), instruction)
                continue
            if command in ("help", "?"):
                self.print_help()
                continue
            if command in ("quit", "q"):
                raise OPLError(
                    "OPL-012",
                    "Debugger Error",
                    "Debug session stopped",
                    instruction.line,
                    instruction.column,
                )

            self.output("Unknown command. Type 'help' for commands.")

    def add_breakpoint(self, target, instruction):
        if ":" in target:
            line_text = target.rsplit(":", 1)[1]
            if not line_text.isdigit():
                self.debugger_error(instruction, f"Invalid breakpoint '{target}'")
            line = int(line_text)
            self.line_breakpoints.add(line)
            self.output(f"Breakpoint set at line {line}")
            return

        if not target.isdigit():
            self.debugger_error(instruction, f"Invalid breakpoint '{target}'")

        value = int(target)
        self.instruction_breakpoints.add(value)
        self.line_breakpoints.add(value)
        self.output(f"Breakpoint set at IP or line {value}")

    def print_call_stack(self, vm):
        self.output("CALL STACK:")
        for frame in vm.frames:
            name = "main" if frame.chunk.name == "<script>" else frame.chunk.name
            self.output(f"- {name}()")

    def print_locals(self, vm):
        for index, frame in enumerate(vm.frames):
            name = "main" if frame.chunk.name == "<script>" else frame.chunk.name
            self.output(f"FRAME {index}: {name}()")
            for key, value in frame.env.values.items():
                self.output(f"  {key} = {self.format_value(value)}")

    def inspect(self, vm, name):
        if not name:
            self.output("Usage: inspect <name>")
            return

        parts = name.split(".")
        value = self.lookup(vm, parts[0])
        if value is None:
            self.output(f"{parts[0]} is undefined")
            return

        for part in parts[1:]:
            value = self.get_child_value(vm, value, part)
            if value is None:
                self.output(f"{name} is undefined")
                return

        self.output(f"{name} = {self.format_value(value)}")

    def lookup(self, vm, name):
        for frame in reversed(vm.frames):
            value = frame.env.get(name)
            if value is not vm.undefined:
                return value
        value = vm.globals.get(name)
        if value is not vm.undefined:
            return value
        return None

    def get_child_value(self, vm, value, name):
        if hasattr(value, "properties") and name in value.properties:
            return value.properties[name]
        if hasattr(value, "values"):
            values = value.values
            if isinstance(values, dict) and name in values:
                return values[name]
        if hasattr(value, "closure"):
            closure_value = value.closure.get(name)
            if closure_value is not vm.undefined:
                return closure_value
        return None

    def print_help(self):
        self.output("Commands:")
        self.output("  step | s              Execute one instruction")
        self.output("  continue | c          Run until next breakpoint or program end")
        self.output("  pause | p             Stay paused")
        self.output("  break <ip|line>       Add instruction/line breakpoint")
        self.output("  break file.opl:<line> Add source-line breakpoint")
        self.output("  stack                 Show call stack")
        self.output("  locals                Show frame locals")
        self.output("  inspect <name>        Show variable or property")
        self.output("  quit | q              Stop debugging")

    def debugger_error(self, instruction, message):
        raise OPLError(
            "OPL-012",
            "Debugger Error",
            message,
            instruction.line,
            instruction.column,
        )

    def format_value(self, value):
        if isinstance(value, list):
            return "[" + ", ".join(self.format_value(item) for item in value) + "]"
        if hasattr(value, "values"):
            return repr(value)
        return repr(value)
