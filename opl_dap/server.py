import json
import sys
import threading

from .adapter import OPLDebugSession


class DAPProtocol:
    def __init__(self):
        self.seq = 1
        self.lock = threading.Lock()
        self.session = OPLDebugSession(self)

    def run(self):
        while True:
            message = self.read_message()
            if message is None:
                break
            self.handle(message)

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
        if length <= 0:
            return None
        return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))

    def send(self, payload):
        with self.lock:
            payload["seq"] = self.seq
            self.seq += 1
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
            sys.stdout.buffer.write(body)
            sys.stdout.buffer.flush()

    def response(self, request, body=None, success=True, message=None):
        payload = {
            "type": "response",
            "request_seq": request.get("seq", 0),
            "command": request.get("command"),
            "success": success,
        }
        if body is not None:
            payload["body"] = body
        if message:
            payload["message"] = message
        self.send(payload)

    def event(self, event, body=None):
        self.send({
            "type": "event",
            "event": event,
            "body": body or {},
        })

    def output(self, text, category="stdout"):
        self.event("output", {"category": category, "output": text})

    def handle(self, request):
        command = request.get("command")
        arguments = request.get("arguments") or {}

        try:
            if command == "initialize":
                self.response(request, self.initialize_response())
                self.event("initialized")
            elif command == "launch":
                self.session.launch(arguments["program"])
                self.response(request)
            elif command == "setBreakpoints":
                lines = [
                    item.get("line")
                    for item in arguments.get("breakpoints", [])
                    if item.get("line") is not None
                ]
                self.response(
                    request,
                    {"breakpoints": self.session.set_breakpoints(lines)},
                )
            elif command == "configurationDone":
                self.response(request)
                self.session.start()
            elif command == "threads":
                self.response(request, {"threads": self.session.threads()})
            elif command == "stackTrace":
                frames = self.session.stack_trace()
                self.response(
                    request,
                    {
                        "stackFrames": frames,
                        "totalFrames": len(frames),
                    },
                )
            elif command == "scopes":
                self.response(
                    request,
                    {"scopes": self.session.scopes(arguments.get("frameId", 1))},
                )
            elif command == "variables":
                self.response(
                    request,
                    {
                        "variables": self.session.variables(
                            arguments.get("variablesReference", 0)
                        )
                    },
                )
            elif command == "continue":
                self.session.continue_execution()
                self.response(request, {"allThreadsContinued": True})
            elif command in ("next", "stepIn"):
                self.session.step()
                self.response(request)
            elif command == "stepOut":
                self.session.step_out()
                self.response(request)
            elif command == "pause":
                self.session.pause()
                self.response(request)
            elif command == "evaluate":
                self.response(
                    request,
                    self.session.evaluate(arguments.get("expression", "")),
                )
            elif command == "disconnect":
                self.session.continue_execution()
                self.response(request)
                self.event("terminated")
            else:
                self.response(request, success=False, message=f"Unsupported command {command}")
        except Exception as error:
            self.response(request, success=False, message=f"OPL-012 Debugger Error: {error}")

    def initialize_response(self):
        return {
            "supportsConfigurationDoneRequest": True,
            "supportsEvaluateForHovers": True,
            "supportsStepInTargetsRequest": False,
            "supportsSetVariable": False,
        }


def main():
    DAPProtocol().run()


if __name__ == "__main__":
    main()
