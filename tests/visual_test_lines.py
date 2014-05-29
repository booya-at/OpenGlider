import openglider.lines as lines
from openglider.graphics import Graphics3D, Line

key_dict = lines.import_lines("../openglider/lines/TEST_INPUT_FILE_1.txt")
thalines = lines.LineSet(key_dict["LINES"][2], key_dict["CALCPAR"][2])
thalines.calc_geo()
thalines.calc_sag()

graphics_lines = [l.get_line_points() for l in thalines.lines]
Graphics3D(map(Line, graphics_lines))
