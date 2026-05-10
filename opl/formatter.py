from opl import lexer, source as source_tools
from opl.errors import OPLError


OPERATORS = {"+", "-", "*", "/", "=", ">", "<", "==", "!="}


def format_source(source):
    tokens = lexer.tokenize(source)
    lines = []
    current = []
    indent = 0

    for token in tokens:
        if token.type == "EOF":
            break
        if token.type == "NEWLINE":
            if current:
                finish_line(lines, current, indent)
            current = []
            continue
        if token.type == "}":
            if current:
                finish_line(lines, current, indent)
            current = []
            indent = max(indent - 4, 0)
            lines.append(" " * indent + "}")
            continue
        if token.type == "{":
            current.append("{")
            finish_line(lines, current, indent)
            current = []
            indent += 4
            continue
        current.append(token)

    finish_line(lines, current, indent)
    return "\n".join(lines).rstrip() + "\n"


def finish_line(lines, items, indent):
    if not items:
        if lines and lines[-1] != "":
            lines.append("")
        return

    text = render_items(items)
    lines.append(" " * indent + text)


def render_items(items):
    text = ""

    for item in items:
        if item == "{":
            text = text.rstrip() + " {"
            continue

        value = token_text(item)

        if item.type in OPERATORS:
            text = text.rstrip() + " " + value + " "
        elif item.type == "(":
            text = text.rstrip() + "("
        elif item.type == ")":
            text = text.rstrip() + ")"
        elif item.type == ",":
            text = text.rstrip() + ", "
        elif item.type == ".":
            text = text.rstrip() + "."
        elif item.type == "[":
            if text.endswith(" "):
                text += "["
            else:
                text = text.rstrip() + "["
        elif item.type == "]":
            text = text.rstrip() + "]"
        elif item.type == ":":
            text = text.rstrip() + ": "
        elif text and not text.endswith((" ", "(", ".", "[")):
            text += " " + value
        else:
            text += value

    return text.rstrip()


def token_text(token):
    if token.type == "STRING":
        return '"' + token.value + '"'
    if token.type == "NUMBER":
        return str(token.value)
    return str(token.value)


def format_file(file_path):
    source_tools.validate_path(file_path)
    source_tools.warn_if_legacy(file_path)

    with open(file_path, "r", encoding="utf-8-sig") as file:
        source = source_tools.normalize_source(file.read())

    formatted = format_source(source)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(formatted)


