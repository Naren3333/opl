class OPLError(Exception):
    def __init__(self, code, title, message, line, column, node_type=None):
        self.code = code
        self.title = title
        self.message = message
        self.line = line
        self.column = column
        self.node_type = node_type

    def __str__(self):
        text = (
            f"{self.code} {self.title}\n"
            f"Line {self.line}, Column {self.column}\n"
        )
        if self.node_type:
            text += f"Node: {self.node_type}\n"
        return text + f"\n{self.message}"


