#!/bin/python2
import sys
import unittest

if len(sys.argv) > 1 and "-a" in sys.argv:
    print("jojo")
    loader = unittest.TestLoader().discover("tests",'*test*.py')
else:
    print("nono")
    loader = unittest.TestLoader().discover("tests")

testresult = unittest.TextTestRunner(verbosity=2).run(loader)