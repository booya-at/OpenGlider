from typing import NamedTuple
import os
from pathlib import Path

import pyupgrade._main  # type: ignore
import autoflake  # type: ignore
import black  # type: ignore
import black.mode  # type: ignore

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

black_args = black.mode.Mode(
    target_versions=set([black.mode.TargetVersion.PY310, black.mode.TargetVersion.PY311]),
    line_length=100,
)

def run() -> None:
    for dirname, x, files in os.walk(basedir / "openglider"):

        for file in files:
            if file.endswith(".py"):
                fullpath = Path(dirname) / file
                print(fullpath)

                pyupgrade._main._fix_file(fullpath, args)
                autoflake.fix_file(fullpath, flake_args)
                black.format_file_in_place(fullpath, fast=False, mode=black_args)

run()