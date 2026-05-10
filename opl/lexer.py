from opl.errors import OPLError


class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column


KEYWORDS = {
    "let": "LET",
    "if": "IF",
    "while": "WHILE",
    "print": "PRINT",
    "fn": "FN",
    "return": "RETURN",
    "import": "IMPORT",
    "model": "MODEL",
    "for": "FOR",
    "in": "IN",
    "true": "TRUE",
    "false": "FALSE",
}


def tokenize(source):
    tokens = []
    index = 0
    line = 1
    column = 1

    while index < len(source):
        char = source[index]

        if char in " \t\r":
            index += 1
            column += 1
        elif char == "\n":
            tokens.append(Token("NEWLINE", "\n", line, column))
            index += 1
            line += 1
            column = 1
        elif char.isalpha() or char == "_":
            start = index
            start_column = column
            while index < len(source) and (
                source[index].isalnum() or source[index] == "_"
            ):
                index += 1
                column += 1
            value = source[start:index]
            tokens.append(Token(KEYWORDS.get(value, "IDENTIFIER"), value, line, start_column))
        elif char.isdigit():
            start = index
            start_column = column
            while index < len(source) and source[index].isdigit():
                index += 1
                column += 1
            tokens.append(Token("NUMBER", int(source[start:index]), line, start_column))
        elif char == '"':
            start_column = column
            index += 1
            column += 1
            start = index
            while index < len(source) and source[index] != '"':
                if source[index] == "\n":
                    raise OPLError(
                        "OPL-002",
                        "Lex Error",
                        "Unterminated string",
                        line,
                        start_column,
                    )
                index += 1
                column += 1
            if index >= len(source):
                raise OPLError(
                    "OPL-002",
                    "Lex Error",
                    "Unterminated string",
                    line,
                    start_column,
                )
            tokens.append(Token("STRING", source[start:index], line, start_column))
            index += 1
            column += 1
        elif char in "{}(),.[]:":
            tokens.append(Token(char, char, line, column))
            index += 1
            column += 1
        elif char in "+-*/><=":
            start_column = column
            if index + 1 < len(source) and source[index:index + 2] == "==":
                tokens.append(Token("==", "==", line, start_column))
                index += 2
                column += 2
            else:
                tokens.append(Token(char, char, line, column))
                index += 1
                column += 1
        elif char == "!":
            if index + 1 < len(source) and source[index:index + 2] == "!=":
                tokens.append(Token("!=", "!=", line, column))
                index += 2
                column += 2
            else:
                raise OPLError("OPL-002", "Lex Error", "Expected '=' after '!'", line, column)
        else:
            raise OPLError(
                "OPL-002",
                "Lex Error",
                f"Unexpected character '{char}'",
                line,
                column,
            )

    tokens.append(Token("EOF", None, line, column))
    return tokens


