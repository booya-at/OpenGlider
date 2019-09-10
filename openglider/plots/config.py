import functools

import numpy as np

from openglider.plots import marks
from openglider.plots.marks import Inside, OnLine
from openglider.utils import Config


class LaserConfig(Config):
    allowance_parallel = 0.01
    allowance_orthogonal = 0.01
    allowance_singleskin = 0.01
    allowance_folded = 0.01
    allowance_general = 0.01
    allowance_diagonals = 0.01
    allowance_trailing_edge = 0.01
    allowance_entry_open = 0.015


sewing_config = {
    "marks": {
        "diagonal": Inside(marks.Triangle()),
        "diagonal_front": Inside(marks.Arrow(left=True)),
        "diagonal_back": Inside(marks.Arrow(left=False)),
        "strap": Inside(marks.Line()),
        "attachment-point": OnLine(marks.Cross(rotation=np.pi / 4)),
        "panel-cut": marks.Line()
    },
    "allowance": {
        "parallel": 0.012,
        "orthogonal": 0.012,
        "singleskin": 0.012,
        "folded": 0.012,
        "general": 0.012,
        "diagonals": 0.012,
        "trailing_edge": 0.024,
        "entry_open": 0.015
    },
    "scale": 1000,
    "layers": {
        "cuts": {
            "id": 'outer',
            "stroke-width": "0.1",
            "stroke": "red",
            "fill": "none"},
        "marks": {
            "id": 'marks',
            "stroke-width": "0.1",
            "stroke": "green",
            "fill": "none"},
        "debug": {
            "id": 'marks',
            "stroke-width": "0.1",
            "stroke": "grey",
            "fill": "none"},
        "inner": {
            "id": "inner",
            "stroke-width": "0.1",
            "stroke": "green",
            "fill": "none"
        },
        "text": {
            "id": 'text',
            "stroke-width": "0.1",
            "stroke": "green",
            "fill": "none"},
        "stitches": {
            "id": "stitches",
            "stroke-width": "0.1",
            "stroke": "black",
            "fill": "none"}
    }

}
