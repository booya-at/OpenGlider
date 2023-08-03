from typing import NamedTuple
import pyupgrade._main
import os
from pathlib import Path

basedir = Path(__file__).absolute().parent

class Args(NamedTuple):
    min_version: tuple[int, int]
    keep_percent_format: bool
    keep_mock: bool
    keep_runtime_typing: bool
    exit_zero_even_if_changed: bool

args = Args((3,10), False, False, False, False)

def run():
    for dirname, x, files in os.walk(basedir / "openglider"):

        for file in files:
            if file.endswith(".py"):
                fullpath = os.path.join(dirname, file)
                print(fullpath)

                pyupgrade._main._fix_file(fullpath, args)

run()