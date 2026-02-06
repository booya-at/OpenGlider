#!/usr/bin/env python
"""
OpenGlider-Tests via pytest ausführen. Ausführliche Doku: tests/README.md.

Usage:
  python testall.py              # nur Unit-Tests (ohne Visual/GUI)
  python testall.py -a           # alle Tests inkl. Visual
  python testall.py -n 3         # Unit-Tests 3× wiederholen
  python testall.py -p "glider"  # nur Tests, deren Name "glider" enthält
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
