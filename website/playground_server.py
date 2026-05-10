import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEBSITE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(ROOT_DIR, "docs")

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from opl import lexer, module_loader, parser, source as source_tools
from opl.errors import OPLError


class PlaygroundHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEBSITE_DIR, **kwargs)

    def do_POST(self):
        if self.path != "/run":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
            code = payload.get("code", "")
            result = run_opl(code)
            self.send_json(200, result)
        except json.JSONDecodeError:
            self.send_json(
                400,
                {
                    "ok": False,
                    "output": "OPL-013 Playground Error\nLine 1, Column 1\n\nInvalid JSON request",
                },
            )

    def translate_path(self, path):
        if path == "/docs":
            path = "/docs/README.md"

        if path.startswith("/docs/"):
            relative_path = path[len("/docs/"):]
            relative_path = relative_path.replace("\\", "/")
            parts = [part for part in relative_path.split("/") if part and part != ".."]
            return os.path.join(DOCS_DIR, *parts)

        return super().translate_path(path)

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def run_opl(code):
    stdout = io.StringIO()

    try:
        normalized = source_tools.normalize_source(code)
        tokens = lexer.tokenize(normalized)
        program = parser.parse(tokens)

        with tempfile.TemporaryDirectory(prefix="opl-playground-") as base_dir:
            with contextlib.redirect_stdout(stdout):
                module_loader.run_program(program, base_dir)

        return {"ok": True, "output": stdout.getvalue()}
    except OPLError as error:
        return {"ok": False, "output": str(error)}
    except Exception as error:
        return {
            "ok": False,
            "output": (
                "OPL-999 Internal Error\n"
                "Line 1, Column 1\n\n"
                f"{error}"
            ),
        }


def main():
    argument_parser = argparse.ArgumentParser(description="Run the local OPL playground server.")
    argument_parser.add_argument("--host", default="127.0.0.1")
    argument_parser.add_argument("--port", default=8787, type=int)
    args = argument_parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), PlaygroundHandler)
    print(f"OPL playground running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
