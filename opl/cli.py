import os
import sys

from opl import formatter, lexer, module_loader, parser, repl, source as source_tools
from opl.__version__ import banner
from opl.diagnostics import check_file
from opl.errors import OPLError
from opl.vm import VirtualMachine, compile_program
from opl.vm.debugger import VMDebugger
from opl.vm.deserializer import load_chunk
from opl.vm.serializer import save_chunk


def main():
    configure_output()

    if len(sys.argv) < 2:
        print_usage()
        return 1

    command = sys.argv[1]

    if command in ("--version", "-v"):
        print(banner())
        return 0

    if command == "repl":
        if len(sys.argv) != 2:
            print_usage()
            return 1
        return repl.start()

    if command == "format":
        if len(sys.argv) != 3:
            print_usage()
            return 1
        return handle_format_command(sys.argv[2])

    if command == "build":
        if len(sys.argv) != 3:
            print_usage()
            return 1
        return handle_build_command(sys.argv[2])

    if command == "inspect":
        if len(sys.argv) != 3:
            print_usage()
            return 1
        return handle_inspect_command(sys.argv[2])

    if command == "debug":
        if len(sys.argv) != 3:
            print_usage()
            return 1
        return handle_file_command(
            "run",
            sys.argv[2],
            use_vm=True,
            debug_bytecode=False,
            debug_gc=False,
            debug_vm=True,
        )

    if command == "check":
        if len(sys.argv) != 3:
            print_usage()
            return 1
        return handle_file_command(
            command,
            sys.argv[2],
            use_vm=False,
            debug_bytecode=False,
            debug_gc=False,
            debug_vm=False,
        )

    if command == "run":
        if len(sys.argv) < 3:
            print_usage()
            return 1
        file_path = sys.argv[2]
        flags = sys.argv[3:]
        valid_flags = {"--vm", "--debug-bytecode", "--debug-gc", "--debug"}
        if any(flag not in valid_flags for flag in flags):
            print_usage()
            return 1
        return handle_file_command(
            command,
            file_path,
            use_vm="--vm" in flags,
            debug_bytecode="--debug-bytecode" in flags,
            debug_gc="--debug-gc" in flags,
            debug_vm="--debug" in flags,
        )

    print_usage()
    return 1


def configure_output():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def print_usage():
    print("Usage: opl run file.opl")
    print("       opl run file.opl --vm")
    print("       opl run file.oplb --vm")
    print("       opl run file.opl --vm --debug-bytecode")
    print("       opl run file.opl --vm --debug-gc")
    print("       opl run file.opl --vm --debug")
    print("       opl debug file.opl")
    print("       opl debug file.oplb")
    print("       opl build file.opl")
    print("       opl inspect file.oplb")
    print("       opl check file.opl")
    print("       opl format file.opl")
    print("       opl repl")
    print("       opl --version")


def print_error(error):
    print(f"{error.code} {error.title}")
    print(f"Line {error.line}, Column {error.column}")
    if error.node_type:
        print(f"Node: {error.node_type}")
    print()
    print(error.message)


def handle_file_command(
    command,
    file_path,
    use_vm=False,
    debug_bytecode=False,
    debug_gc=False,
    debug_vm=False,
):
    try:
        source_tools.validate_run_path(file_path)
        source_tools.warn_if_legacy(file_path)

        if command == "check":
            return handle_check_command(file_path)

        if file_path.endswith(source_tools.BYTECODE_EXTENSION):
            if not use_vm:
                raise OPLError(
                    "OPL-011",
                    "Bytecode Error",
                    "Compiled .oplb files must be run with --vm",
                    1,
                    1,
                )
            chunk = load_chunk(file_path)
            if debug_bytecode:
                print(chunk.disassemble())
            run_chunk(chunk, file_path, debug_gc, debug_vm)
            return 0

        with open(file_path, "r", encoding="utf-8-sig") as file:
            source = source_tools.normalize_source(file.read())

        tokens = lexer.tokenize(source)
        program = parser.parse(tokens)

        if use_vm:
            chunk = compile_program(program)
            if debug_bytecode:
                print(chunk.disassemble())
            run_chunk(chunk, file_path, debug_gc, debug_vm)
        else:
            base_dir = os.path.dirname(os.path.abspath(file_path))
            module_loader.run_program(program, base_dir)

        return 0
    except OPLError as error:
        print_error(error)
        return 1
    except OSError as error:
        print(f"OPL-004 File Error\nLine 1, Column 1\n\n{error}")
        return 1
    except Exception as error:
        print(f"OPL-999 Internal Error\nLine 1, Column 1\n\n{error}")
        return 1


def run_chunk(chunk, file_path, debug_gc=False, debug_vm=False):
    base_dir = os.path.dirname(os.path.abspath(file_path))
    debugger = VMDebugger() if debug_vm else None
    VirtualMachine(debug_gc=debug_gc, base_dir=base_dir, debugger=debugger).run(chunk)


def handle_build_command(file_path):
    try:
        source_tools.validate_path(file_path)
        with open(file_path, "r", encoding="utf-8-sig") as file:
            source = source_tools.normalize_source(file.read())

        program = parser.parse(lexer.tokenize(source))
        chunk = compile_program(program)
        output_path = os.path.splitext(file_path)[0] + source_tools.BYTECODE_EXTENSION
        save_chunk(chunk, output_path)
        print(f"Built {output_path}")
        return 0
    except OPLError as error:
        print_error(error)
        return 1
    except OSError as error:
        print(f"OPL-004 File Error\nLine 1, Column 1\n\n{error}")
        return 1
    except Exception as error:
        print(f"OPL-999 Internal Error\nLine 1, Column 1\n\n{error}")
        return 1


def handle_inspect_command(file_path):
    try:
        source_tools.validate_bytecode_path(file_path)
        chunk = load_chunk(file_path)
        print(chunk.disassemble())
        return 0
    except OPLError as error:
        print_error(error)
        return 1
    except OSError as error:
        print(f"OPL-004 File Error\nLine 1, Column 1\n\n{error}")
        return 1
    except Exception as error:
        print(f"OPL-999 Internal Error\nLine 1, Column 1\n\n{error}")
        return 1


def handle_check_command(file_path):
    diagnostics = check_file(file_path)

    print("OPL Diagnostics")
    print()

    if not diagnostics:
        print("No issues found")
        return 0

    for index, diagnostic in enumerate(diagnostics):
        if index:
            print()
        label = "Error" if diagnostic.severity == "error" else "Warning"
        print(f"{label}: {diagnostic.message}")
        print(f"Line {diagnostic.line}, Column {diagnostic.column}")
        print(f"Code: {diagnostic.code}")

    return 1 if any(d.severity == "error" for d in diagnostics) else 0


def handle_format_command(file_path):
    try:
        formatter.format_file(file_path)
        print("Formatting complete")
        return 0
    except OPLError as error:
        print_error(error)
        return 1
    except OSError as error:
        print(f"OPL-004 File Error\nLine 1, Column 1\n\n{error}")
        return 1
    except Exception as error:
        print(f"OPL-999 Internal Error\nLine 1, Column 1\n\n{error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
