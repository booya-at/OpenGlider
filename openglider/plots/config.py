import functools

import numpy

from openglider.plots import marks
from openglider.plots.marks import Inside, OnLine

sewing_config = {
    "marks": {
        "diagonal": Inside(marks.triangle),
        "diagonal_front": Inside(marks.arrow_left),
        "diagonal_back": Inside(marks.arrow_right),
        "strap": Inside(marks.line),
        "attachment-point": OnLine(functools.partial(marks.cross, rotation=numpy.pi / 4)),
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
        {"cuts": {
            "id": 'outer',
            "stroke-width": "0.001",
            "stroke": "red",
            "fill": "none"},
         "marks": {
             "id": 'marks',
             "stroke-width": "0.001",
             "stroke": "green",
             "fill": "none"},
         "text": {
             "id": 'text',
             "stroke-width": "0.001",
             "stroke": "green",
             "fill": "none"},
         "stitches": {
             "id": "stitches",
             "stroke-width": "0.001",
             "stroke": "black",
             "fill": "none"}
         }


}