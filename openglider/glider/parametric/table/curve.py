from __future__ import annotations

from typing import Any, Type
from packaging.version import Version
from openglider.glider.parametric.table.base import TableType

from openglider.version import version
from openglider.utils.table import Table
from openglider.glider.shape import Shape
import openglider.glider.curve


class CurveTable:
    table_type = TableType.general
    table_name = "Curves"

    def __init__(self, table: Table | None=None, openglider_version: Version=version):
        if table is None:
            self.table = Table()
        else:
            self.table = table or Table()

            if openglider_version < Version("0.1.3"):
                self.table = migrate_0_1_2(self.table)

        self.table.name = self.table_name

    def __json__(self) -> dict[str, Any]:
        return {
            "table": self.table
        }

    def get_curves(self, shape: Shape) -> dict[str, openglider.glider.curve.GliderCurveType]:
        curves = {}
        column = 0
        curve_columns = 2

        while column < self.table.num_columns:
            name = self.table[0, column+1]
            curve_type = self.table[1, column+1] or "Curve"
            curve_unit = self.table[2, column+1]

            points = []

            for row in range(3, self.table.num_rows):
                coords = [self.table[row, column+i] for i in range(curve_columns)]

                if any([c is None for c in coords]):
                    break

                points.append(coords)
            
            try:
                curve_cls: Type[openglider.glider.curve.Curve] = getattr(openglider.glider.curve, curve_type)
            except Exception:
                raise Exception(f"invalid curve type: {curve_type}")
            curve_instance = curve_cls(points, shape)
            curve_instance.unit = curve_unit

            curves[name] = curve_instance 

            column += curve_columns
        
        return curves
    
    def apply_curves(self, curves: dict[str, openglider.glider.curve.GliderCurveType]) -> Table:
        self.table = Table(name=self.table_name)
        column = 0

        for name, curve in curves.items():
            self.table[0, column] = name
            self.table[0, column + 1] = curve.__class__.__name__

            for row, point in enumerate(curve.controlpoints):
                self.table[row+1, column] = point[0]
                self.table[row+1, column+1] = point[1]
            
            column += 2
        
        return self.table



def migrate_0_1_2(table: Table) -> Table:
    new_table = Table()
    
    column = 0
    while column < table.num_columns:
        new_column = Table()
        new_column.insert_row(["Name", table[0, column]])
        new_column.insert_row(["Type", table[0,  column+1]])
        new_column.insert_row(["Unit", None])
        old_column = table.get_columns(column, column+2)

        new_column.append_bottom(old_column.get_rows(1, old_column.num_rows))

        new_table.append_right(new_column)
        column += 2
    
    return new_table