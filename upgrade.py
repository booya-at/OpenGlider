from typing import NamedTuple
import os
from pathlib import Path

import pyupgrade._main
import autoflake

basedir = Path(__file__).absolute().parent

class Args(NamedTuple):
    min_version: tuple[int, int]
    keep_percent_format: bool
    keep_mock: bool
    keep_runtime_typing: bool
    exit_zero_even_if_changed: bool

args = Args((3,10), False, False, False, False)
flake_args = {
    "write_to_stdout": False,
    "ignore_init_module_imports": True,
    "expand_star_imports": True,
    "remove_all_unused_imports": True,
    "remove_duplicate_keys": True,
    "remove_unused_variables": True,
    "remove_rhs_for_unused_variables": True,
    "ignore_pass_statements": False,
    "ignore_pass_after_docstring": False,
    "check": False,
    "check_diff": False,
    "in_place": True,

}

def run():
    for dirname, x, files in os.walk(basedir / "openglider"):

        for file in files:
            if file.endswith(".py"):
                fullpath = os.path.join(dirname, file)
                print(fullpath)

                pyupgrade._main._fix_file(fullpath, args)
                autoflake.fix_file(fullpath, flake_args)

run()