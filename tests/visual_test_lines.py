import unittest
import os
import numpy as np

from openglider.lines.import_text import import_lines
from openglider.lines import LineSet
import openglider.graphics as graph


test_dir = os.path.dirname(os.path.abspath(__file__))


class TestLines(unittest.TestCase):
    def setUp(self):
        pass

    def runcase(self, path):
        key_dict = import_lines(path)
        # print(key_dict["LINES"][2])
        thalines = LineSet(
            key_dict["LINES"][2], np.array([100, 0, 1]))
        # for line in thalines.lines:
        #     line.lineset = thalines
        
        for _ in range(3):
            thalines.recalc(True)
        objects = map(lambda line: graph.Line(line.get_line_points(100)), thalines.lines)
        graph.Graphics3D(objects)

    def test_case_1(self):
        self.runcase(test_dir+"/lines/TEST_INPUT_FILE_1.txt")

    def test_case_2(self):
        self.runcase(test_dir+"/lines/TEST_INPUT_FILE_2.txt")

    def test_case_3(self):
        self.runcase(test_dir+"/lines/TEST_INPUT_FILE_3.txt")

    def test_case_4(self):
        self.runcase(test_dir+"/lines/TEST_INPUT_FILE_4.txt")


if __name__ == '__main__':
    unittest.main(verbosity=2)