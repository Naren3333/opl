from opl.errors import OPLError


def to_core(source):
    lines = source.splitlines()
    output = []
    indent_stack = [0]

    for line_number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip():
            output.append("")
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        text = raw_line.strip()

        while indent < indent_stack[-1]:
            indent_stack.pop()
            output.append(" " * indent_stack[-1] + "}")

        if text == "}":
            continue

        if indent > indent_stack[-1]:
            raise OPLError(
                "OPL-005",
                "Pirate Syntax Error",
                "Unexpected indentation",
                line_number,
                1,
            )

        converted = convert_line(text, line_number)
        output.append(" " * indent + converted)

        if text.endswith(":") or converted.endswith("{"):
            indent_stack.append(indent + 4)

    while len(indent_stack) > 1:
        indent_stack.pop()
        output.append(" " * indent_stack[-1] + "}")

    return "\n".join(output)


def convert_line(text, line_number):
    if text.startswith("bounty "):
        body = text[len("bounty "):]
        if "=" not in body:
            raise pirate_error("Expected '=' in bounty statement", line_number, 1)
        return "let " + body

    if text.startswith("say "):
        value = text[len("say "):].strip()
        if not value:
            raise pirate_error("Expected value after say", line_number, 1)
        return "print(" + value + ")"

    if text.startswith("dfruit "):
        if not text.endswith(":"):
            raise pirate_error(
                "Expected ':' after dfruit declaration",
                line_number,
                len(text),
            )
        signature = text[len("dfruit "):-1].strip()
        if not signature:
            raise pirate_error("Expected function name after dfruit", line_number, 1)
        return "fn " + signature + " {"

    if text.startswith("model "):
        if not text.endswith(":"):
            raise pirate_error("Expected ':' after model declaration", line_number, len(text))
        name = text[len("model "):-1].strip()
        if not name:
            raise pirate_error("Expected model name after model", line_number, 1)
        return "model " + name + " {"

    if text.startswith("return "):
        value = text[len("return "):].strip()
        if not value:
            raise pirate_error("Expected value after return", line_number, 1)
        return "return " + value

    if text.startswith("if "):
        if not text.endswith(":"):
            raise pirate_error("Expected ':' after if condition", line_number, len(text))
        condition = text[len("if "):-1].strip()
        if not condition:
            raise pirate_error("Expected condition after if", line_number, 1)
        return "if " + condition + " {"

    if text.startswith("while "):
        if not text.endswith(":"):
            raise pirate_error("Expected ':' after while condition", line_number, len(text))
        condition = text[len("while "):-1].strip()
        if not condition:
            raise pirate_error("Expected condition after while", line_number, 1)
        return "while " + condition + " {"

    if text.startswith("for "):
        if not text.endswith(":"):
            raise pirate_error("Expected ':' after for loop", line_number, len(text))
        loop = text[:-1].strip()
        return loop + " {"

    if text.startswith("import "):
        return text

    if text.endswith(")") or text.endswith("]") or text.endswith("}"):
        return text

    if ":" in text and (text.startswith('"') or text[0].isdigit()):
        return text

    if "[" in text and "=" in text:
        return text

    if "." in text and ("=" in text or text.endswith(")")):
        return text

    raise pirate_error("Unknown Pirate statement", line_number, 1)


def pirate_error(message, line, column):
    return OPLError("OPL-005", "Pirate Syntax Error", message, line, column)


