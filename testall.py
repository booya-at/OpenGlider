#!/usr/bin/env python
"""
Run OpenGlider tests via pytest.

Usage:
  python testall.py           # unit tests only (excludes visual/GUI tests)
  python testall.py -a       # all tests including visual
  python testall.py -n 3     # run unit tests 3 times
  python testall.py -p "test_glider"  # run tests matching pattern

Equivalent pytest commands:
  pytest tests/ -m "not visual"
  pytest tests/
  pytest tests/ -m "not visual" --count=3
  pytest tests/ -k "test_glider"
"""

import sys
import subprocess


def main():
    args = sys.argv[1:]
    run_all = "-a" in args or "--run_all" in args or "--run-all" in args
    if run_all:
        args = [a for a in args if a not in ("-a", "--run_all", "--run-all")]
    pytest_args = ["tests/", "-v"]
    if not run_all:
        pytest_args.extend(["-m", "not visual"])

    # Optional: -n N to repeat tests N times
    num = 1
    if "-n" in args or "--num" in args:
        try:
            i = args.index("-n") if "-n" in args else args.index("--num")
            num = int(args[i + 1])
            args = args[:i] + args[i + 2 :]
        except (IndexError, ValueError):
            pass
    if "-p" in args or "--pattern" in args:
        try:
            i = args.index("-p") if "-p" in args else args.index("--pattern")
            pattern = args[i + 1]
            pytest_args.extend(["-k", pattern])
            args = args[:i] + args[i + 2 :]
        except IndexError:
            pass

    # Filter out remaining OptionParser-style options pytest doesn't know
    args = [a for a in args if a not in ("-f", "--folder", "-v", "--verbose") and not a.startswith("--folder=")]

    pytest_args = [sys.executable, "-m", "pytest"] + pytest_args + args

    for run in range(num):
        if num > 1:
            print(f"\n>>> Run ({run + 1}/{num})")
        result = subprocess.run(pytest_args)
        if result.returncode != 0:
            sys.exit(result.returncode)
    sys.exit(0)


if __name__ == "__main__":
    main()
