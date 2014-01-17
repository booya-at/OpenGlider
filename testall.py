#!/bin/python2
import sys
import unittest
if len(sys.argv) > 2 and "-h" in sys.argv:
    print("Run Tests: -a for all tests, no argument for all automated, -p for a specified pattern (eg.: Profile")
elif len(sys.argv) > 1 and "-a" in sys.argv:
    print("running visual tests")
    loader = unittest.TestLoader().discover("tests",'*test*.py')
elif len(sys.argv) > 1 and "-p" in sys.argv:
    loader = unittest.TestLoader().discover("tests",'*test*.py')
else:
    print("only automated tests (use -a for all)")
    loader = unittest.TestLoader().discover("tests", 'test*.py')

test_results = unittest.TextTestRunner(verbosity=2).run(loader)