import re

from opl.errors import OPLError
from opl.frontend import pirate_parser


OFFICIAL_EXTENSION = ".opl"
BYTECODE_EXTENSION = ".oplb"
LEGACY_EXTENSIONS = (".oppl",)
ALL_EXTENSIONS = (OFFICIAL_EXTENSION,) + LEGACY_EXTENSIONS
RUN_EXTENSIONS = ALL_EXTENSIONS + (BYTECODE_EXTENSION,)

PIRATE_KEYWORDS = ("bounty", "dfruit", "say")


def validate_path(file_path):
    if file_path.endswith(ALL_EXTENSIONS):
        return

    raise OPLError(
        "OPL-008",
        "File Error",
        "OPL source files must use the .opl extension",
        1,
        1,
    )


def validate_run_path(file_path):
    if file_path.endswith(RUN_EXTENSIONS):
        return

    raise OPLError(
        "OPL-008",
        "File Error",
        "OPL files must use .opl or .oplb",
        1,
        1,
    )


def validate_bytecode_path(file_path):
    if file_path.endswith(BYTECODE_EXTENSION):
        return

    raise OPLError(
        "OPL-008",
        "File Error",
        "Compiled OPL files must use the .oplb extension",
        1,
        1,
    )


def warn_if_legacy(file_path):
    if file_path.endswith(LEGACY_EXTENSIONS):
        print("Warning: deprecated extension; use .opl instead")


def normalize_source(source):
    if is_pirate_source(source):
        return pirate_parser.to_core(source)
    return source


def is_pirate_source(source):
    for keyword in PIRATE_KEYWORDS:
        if re.search(rf"(^|\s){keyword}(\s|\()", source):
            return True
    return False


