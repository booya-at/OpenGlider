# -*- coding: utf-8 -*-
from line_set import LineSet
from elements import Line, Node
from import_text import import_lines


if __name__ == "__main__":
    key_dict = import_lines("TEST_INPUT_FILE_2.txt")
    thalines = LineSet(
        key_dict["LINES"][2], key_dict["CALCPAR"][2])
    thalines.calc_geo()
    thalines.calc_sag()
