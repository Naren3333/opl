import json

from opl.errors import OPLError
from opl.vm.chunk import Chunk
from opl.vm.compiler import CompiledFunction
from opl.vm.serializer import MAGIC, VERSION


def load_chunk(file_path):
    try:
        with open(file_path, "r", encoding="utf-8-sig") as file:
            data = json.load(file)
    except OSError as error:
        raise OPLError("OPL-004", "File Error", str(error), 1, 1)
    except json.JSONDecodeError as error:
        raise OPLError("OPL-011", "Bytecode Error", str(error), 1, 1)

    if data.get("magic") != MAGIC:
        raise OPLError(
            "OPL-011",
            "Bytecode Error",
            "Invalid OPL bytecode file",
            1,
            1,
        )

    if data.get("version") != VERSION:
        raise OPLError(
            "OPL-011",
            "Bytecode Version Error",
            f"Unsupported bytecode version {data.get('version')}",
            1,
            1,
        )

    return chunk_from_data(data["chunk"])


def chunk_from_data(data):
    chunk = Chunk(data["name"])
    for item in data["instructions"]:
        chunk.emit(
            item["opcode"],
            operand_from_data(item["operand"]),
            item["line"],
            item["column"],
        )
    return chunk


def operand_from_data(data):
    operand_type = data["type"]

    if operand_type == "function":
        return CompiledFunction(
            data["name"],
            data["parameters"],
            chunk_from_data(data["chunk"]),
            data["line"],
            data["column"],
        )

    if operand_type == "tuple":
        return tuple(operand_from_data(item) for item in data["items"])

    if operand_type == "list":
        return [operand_from_data(item) for item in data["items"]]

    if operand_type == "value":
        return data["value"]

    raise OPLError(
        "OPL-011",
        "Bytecode Error",
        f"Unknown bytecode operand type '{operand_type}'",
        1,
        1,
    )
