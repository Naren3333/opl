class Instruction:
    def __init__(self, opcode, operand=None, line=1, column=1):
        self.opcode = opcode
        self.operand = operand
        self.line = line
        self.column = column


class Chunk:
    def __init__(self, name="<script>"):
        self.name = name
        self.instructions = []

    def emit(self, opcode, operand=None, line=1, column=1):
        self.instructions.append(Instruction(opcode, operand, line, column))
        return len(self.instructions) - 1

    def patch(self, index, operand):
        self.instructions[index].operand = operand

    def current_offset(self):
        return len(self.instructions)

    def disassemble(self):
        lines = []
        for index, instruction in enumerate(self.instructions):
            if instruction.operand is None:
                lines.append(f"{index:04d} {instruction.opcode}")
            else:
                lines.append(f"{index:04d} {instruction.opcode} {instruction.operand}")
        for instruction in self.instructions:
            operand = instruction.operand
            if hasattr(operand, "chunk"):
                lines.append("")
                lines.append(f"-- {operand.name} --")
                lines.append(operand.chunk.disassemble())
        return "\n".join(lines)
