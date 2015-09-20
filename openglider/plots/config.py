import numpy
import functools

from openglider.plots import marks


def inside(fctn):
    """
    Put two profile points (outer, inner) on the inside of sewing mark
    :param fctn:
    :return:
    """
    return lambda p1, p2: fctn(2 * p1 - p2, p1)


def on_line(fctn):
    return lambda p1, p2: fctn(0.5 * (p1 + p2), 1.5 * p1 - 0.5 * p2)


sewing_config = {
    "marks": {
        "diagonal": inside(marks.triangle),
        "diagonal_front": inside(marks.arrow_left),
        "diagonal_back": inside(marks.arrow_right),
        "strap": inside(marks.line),
        "attachment-point": on_line(functools.partial(marks.cross, rotation=numpy.pi/4)),
        "panel-cut": marks.line
    },
    "allowance": {
        "parallel": 0.012,
        "orthogonal": 0.012,
        "folded": 0.012,
        "general": 0.012,
        "diagonals": 0.012,
        "trailing_edge": 0.024,
        "entry_open": 0.015
    },
    "scale": 1000,
    "layers":
        {"Cuts": {
            "id": 'outer',
            "stroke_width": "0.001",
            "stroke": "green",
            "fill": "none"},
         "Marks": {
             "id": 'marks',
             "stroke_width": "0.001",
             "stroke": "black",
             "fill": "none"},
         "Text": {
             "id": 'text',
             "stroke_width": "0.001",
             "stroke": "black",
             "fill": "none"},
         "Stitches": {
             "id": "stitches",
             "stroke_width": "0.001",
             "stroke": "grey",
             "fill": "none"}
         }


}