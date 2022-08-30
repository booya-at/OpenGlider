from typing import Dict, Any
from openglider.glider.parametric.table.elements import TableType

from openglider.utils.table import Table
from openglider.glider.shape import Shape
import openglider.glider.curve


class CurveTable:
    table_type = TableType.general

    def __init__(self, table: Table=None):
        self.table = table or Table()
        self.table.name = "Curves"

    def __json__(self):
        return {
            "table": self.table
        }

    def get_curves(self, shape: Shape):
        curves = {}
        column = 0
        curve_columns = 2

        while column < self.table.num_columns:
            name = self.table[0, column]
            curve_type = self.table[0, column + 1] or "Curve"
            points = []

            for row in range(1, self.table.num_rows):
                coords = [self.table[row, column+i] for i in range(curve_columns)]

                if any([c is None for c in coords]):
                    break

                points.append(coords)
            
            try:
                curve_cls = getattr(openglider.glider.curve, curve_type)
            except:
                raise Exception(f"invalid curve type: {curve_type}")
            curves[name] = curve_cls(points, shape)

            column += curve_columns
        
        return curves
    
    def apply_curves(self, curves: Dict[str, Any]):
        self.table = Table()
        column = 0

        for name, curve in curves.items():
            self.table[0, column] = name
            self.table[0, column + 1] = curve.__class__.__name__

            for row, point in enumerate(curve.controlpoints):
                self.table[row+1, column] = point[0]
                self.table[row+1, column+1] = point[1]
            
            column += 2
        
        return self.table



