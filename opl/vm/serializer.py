import json

from opl.vm.compiler import CompiledFunction


MAGIC = "OPLB"
VERSION = 1


def save_chunk(chunk, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(serialize_chunk(chunk), file, indent=2)


def serialize_chunk(chunk):
    return {
        "magic": MAGIC,
        "version": VERSION,
        "chunk": chunk_to_data(chunk),
    }


def chunk_to_data(chunk):
    return {
        "name": chunk.name,
        "instructions": [
            {
                "opcode": instruction.opcode,
                "operand": operand_to_data(instruction.operand),
                "line": instruction.line,
                "column": instruction.column,
            }
            for instruction in chunk.instructions
        ],
    }


def operand_to_data(operand):
    if isinstance(operand, CompiledFunction):
        return {
            "type": "function",
            "name": operand.name,
            "parameters": operand.parameters,
            "line": operand.line,
            "column": operand.column,
            "chunk": chunk_to_data(operand.chunk),
        }

    if isinstance(operand, tuple):
        return {
            "type": "tuple",
            "items": [operand_to_data(item) for item in operand],
        }

    if isinstance(operand, list):
        return {
            "type": "list",
            "items": [operand_to_data(item) for item in operand],
        }

    return {
        "type": "value",
        "value": operand,
    }
