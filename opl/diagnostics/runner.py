import json
import os
import sys

from opl.diagnostics.core import check_file, check_source


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--stdin":
        file_path = sys.argv[2]
        source = sys.stdin.read()
        base_dir = os.path.dirname(os.path.abspath(file_path))
        diagnostics = check_source(source, base_dir)
        print(json.dumps([diagnostic.to_dict() for diagnostic in diagnostics]))
        return 0

    if len(sys.argv) != 2:
        print(json.dumps([
            {
                "message": "Usage: python -m opl.diagnostics.runner [--stdin] file.opl",
                "severity": "error",
                "line": 1,
                "column": 1,
                "code": "OPL-D000",
            }
        ]))
        return 1

    diagnostics = check_file(sys.argv[1])
    print(json.dumps([diagnostic.to_dict() for diagnostic in diagnostics]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
