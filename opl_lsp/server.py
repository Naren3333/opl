import json
import os
import sys
import traceback

from opl.diagnostics import check_source
from .symbols import (
    COMPLETION_CLASS,
    COMPLETION_FUNCTION,
    COMPLETION_METHOD,
    COMPLETION_VARIABLE,
    KIND_CLASS,
    KIND_FUNCTION,
    KIND_METHOD,
    KIND_MODULE,
    KIND_VARIABLE,
    Symbol,
    build_document_index,
    path_to_uri,
    read_file_index,
    stdlib_symbols,
    uri_to_path,
    word_at,
)


TEXT_SYNC_FULL = 1
DIAGNOSTIC_ERROR = 1
DIAGNOSTIC_WARNING = 2


class OPLLspServer:
    def __init__(self):
        self.documents = {}
        self.workspace_roots = []
        self.stdlib_symbols = stdlib_symbols()
        self.shutdown_requested = False

    def run(self):
        while True:
            message = self.read_message()
            if message is None:
                break
            self.handle_message(message)

    def read_message(self):
        headers = {}

        while True:
            line = sys.stdin.buffer.readline()
            if not line:
                return None
            if line in (b"\r\n", b"\n"):
                break
            name, value = line.decode("ascii").split(":", 1)
            headers[name.lower()] = value.strip()

        length = int(headers.get("content-length", "0"))
        if length == 0:
            return None

        body = sys.stdin.buffer.read(length)
        return json.loads(body.decode("utf-8"))

    def send(self, payload):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        sys.stdout.buffer.write(header + body)
        sys.stdout.buffer.flush()

    def respond(self, request_id, result=None, error=None):
        response = {"jsonrpc": "2.0", "id": request_id}
        if error:
            response["error"] = error
        else:
            response["result"] = result
        self.send(response)

    def notify(self, method, params):
        self.send({"jsonrpc": "2.0", "method": method, "params": params})

    def handle_message(self, message):
        method = message.get("method")
        request_id = message.get("id")
        params = message.get("params") or {}

        try:
            if method == "initialize":
                self.respond(request_id, self.initialize(params))
            elif method == "shutdown":
                self.shutdown_requested = True
                self.respond(request_id, None)
            elif method == "exit":
                raise SystemExit(0 if self.shutdown_requested else 1)
            elif method == "textDocument/didOpen":
                self.did_open(params)
            elif method == "textDocument/didChange":
                self.did_change(params)
            elif method == "textDocument/didClose":
                self.did_close(params)
            elif method == "workspace/didChangeWatchedFiles":
                self.did_change_watched_files(params)
            elif method == "textDocument/completion":
                self.respond(request_id, self.completion(params))
            elif method == "textDocument/hover":
                self.respond(request_id, self.hover(params))
            elif method == "textDocument/definition":
                self.respond(request_id, self.definition(params))
            elif method == "textDocument/documentSymbol":
                self.respond(request_id, self.document_symbols(params))
            elif method == "workspace/symbol":
                self.respond(request_id, self.workspace_symbols(params))
            elif request_id is not None:
                self.respond(request_id, None)
        except Exception as error:
            traceback.print_exc(file=sys.stderr)
            if request_id is not None:
                self.respond(
                    request_id,
                    error={
                        "code": -32603,
                        "message": str(error),
                    },
                )

    def initialize(self, params):
        self.workspace_roots = self.get_workspace_roots(params)
        self.scan_workspace()
        return {
            "capabilities": {
                "textDocumentSync": TEXT_SYNC_FULL,
                "hoverProvider": True,
                "definitionProvider": True,
                "documentSymbolProvider": True,
                "workspaceSymbolProvider": True,
                "completionProvider": {
                    "resolveProvider": False,
                    "triggerCharacters": [".", "(", " "],
                },
            },
            "serverInfo": {"name": "opl-lsp", "version": "0.1.0"},
        }

    def get_workspace_roots(self, params):
        roots = []
        for folder in params.get("workspaceFolders") or []:
            if folder.get("uri"):
                roots.append(uri_to_path(folder["uri"]))
        if not roots and params.get("rootUri"):
            roots.append(uri_to_path(params["rootUri"]))
        return [root for root in roots if root and os.path.isdir(root)]

    def scan_workspace(self):
        for root in self.workspace_roots:
            for current, dirs, files in os.walk(root):
                dirs[:] = [
                    name
                    for name in dirs
                    if name not in {".git", "node_modules", "dist", "out", "__pycache__"}
                ]
                for file_name in files:
                    if file_name.endswith(".opl"):
                        path = os.path.join(current, file_name)
                        try:
                            index = read_file_index(path)
                            self.documents[index.uri] = index
                        except OSError:
                            pass

    def did_open(self, params):
        text_document = params["textDocument"]
        self.update_document(text_document["uri"], text_document.get("text", ""))

    def did_change(self, params):
        uri = params["textDocument"]["uri"]
        changes = params.get("contentChanges") or []
        if changes:
            self.update_document(uri, changes[-1].get("text", ""))

    def did_close(self, params):
        uri = params["textDocument"]["uri"]
        path = uri_to_path(uri)
        if os.path.exists(path):
            try:
                self.documents[uri] = read_file_index(path)
            except OSError:
                self.documents.pop(uri, None)
        else:
            self.documents.pop(uri, None)
        self.notify("textDocument/publishDiagnostics", {"uri": uri, "diagnostics": []})

    def did_change_watched_files(self, params):
        for change in params.get("changes") or []:
            uri = change.get("uri")
            if not uri:
                continue
            path = uri_to_path(uri)
            if os.path.exists(path):
                try:
                    self.documents[uri] = read_file_index(path)
                except OSError:
                    self.documents.pop(uri, None)
            else:
                self.documents.pop(uri, None)

    def update_document(self, uri, source):
        self.documents[uri] = build_document_index(uri, source)
        self.publish_diagnostics(uri, source)

    def publish_diagnostics(self, uri, source):
        path = uri_to_path(uri)
        base_dir = os.path.dirname(os.path.abspath(path))
        diagnostics = []
        for diagnostic in check_source(source, base_dir):
            diagnostics.append(
                {
                    "range": self.range_from_line_column(
                        diagnostic.line,
                        diagnostic.column,
                    ),
                    "severity": (
                        DIAGNOSTIC_WARNING
                        if diagnostic.severity == "warning"
                        else DIAGNOSTIC_ERROR
                    ),
                    "code": diagnostic.code,
                    "source": "OPL",
                    "message": diagnostic.message,
                }
            )
        self.notify("textDocument/publishDiagnostics", {"uri": uri, "diagnostics": diagnostics})

    def range_from_line_column(self, line, column):
        start_line = max(line - 1, 0)
        start_char = max(column - 1, 0)
        return {
            "start": {"line": start_line, "character": start_char},
            "end": {"line": start_line, "character": start_char + 1},
        }

    def completion(self, params):
        current_uri = params["textDocument"]["uri"]
        items = []
        seen = set()

        for symbol in self.all_symbols(current_uri):
            key = (symbol.name, symbol.kind)
            if key in seen:
                continue
            seen.add(key)
            kind = {
                "function": COMPLETION_FUNCTION,
                "module": COMPLETION_CLASS,
                "model": COMPLETION_CLASS,
                "method": COMPLETION_METHOD,
                "variable": COMPLETION_VARIABLE,
            }.get(symbol.kind, COMPLETION_VARIABLE)
            items.append(
                {
                    "label": symbol.name,
                    "kind": kind,
                    "detail": symbol.detail,
                    "data": {"uri": symbol.uri, "line": symbol.line, "column": symbol.column},
                }
            )

        return {"isIncomplete": False, "items": items}

    def hover(self, params):
        symbol = self.resolve_symbol_at(params)
        if not symbol:
            return None
        return {
            "contents": {
                "kind": "markdown",
                "value": f"**{symbol.detail}**\n\nDefined at line {symbol.line}",
            },
            "range": symbol.range(),
        }

    def definition(self, params):
        symbol = self.resolve_symbol_at(params)
        if not symbol:
            return None
        return symbol.location()

    def document_symbols(self, params):
        uri = params["textDocument"]["uri"]
        document = self.documents.get(uri)
        if not document:
            return []
        return document.outline

    def workspace_symbols(self, params):
        query = (params.get("query") or "").lower()
        results = []

        for symbol in self.all_symbols():
            if query and query not in symbol.name.lower():
                continue
            kind = {
                "function": KIND_FUNCTION,
                "module": KIND_MODULE,
                "model": KIND_CLASS,
                "method": KIND_METHOD,
                "variable": KIND_VARIABLE,
            }.get(symbol.kind, KIND_VARIABLE)
            results.append(
                {
                    "name": (
                        f"{symbol.container}.{symbol.name}"
                        if symbol.kind == "method" and symbol.container
                        else symbol.name
                    ),
                    "kind": kind,
                    "location": symbol.location(),
                    "containerName": symbol.container,
                }
            )

        return results

    def resolve_symbol_at(self, params):
        uri = params["textDocument"]["uri"]
        position = params["position"]
        document = self.documents.get(uri)
        if not document:
            return None
        name = word_at(document.source, position)
        if not name:
            return None

        local = self.best_symbol(document.symbols_named(name), position)
        if local:
            return local

        return self.best_symbol(
            [symbol for symbol in self.all_symbols(uri) if symbol.name == name],
            position,
        )

    def best_symbol(self, symbols, position):
        if not symbols:
            return None
        target_line = position.get("line", 0) + 1
        before = [symbol for symbol in symbols if symbol.line <= target_line]
        if before:
            return sorted(before, key=lambda item: (item.line, item.column))[-1]
        return sorted(symbols, key=lambda item: (item.line, item.column))[0]

    def all_symbols(self, current_uri=None):
        symbols = list(self.stdlib_symbols)
        if current_uri and current_uri in self.documents:
            symbols.extend(self.documents[current_uri].symbols)

        for uri, document in self.documents.items():
            if uri == current_uri:
                continue
            symbols.extend(document.symbols)

        return symbols


def main():
    OPLLspServer().run()


if __name__ == "__main__":
    main()
