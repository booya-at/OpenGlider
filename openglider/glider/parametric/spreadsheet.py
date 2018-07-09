import collections
import math
import copy

import pyexcel_ods3
import pyexcel_xls

from openglider.glider.cell import DiagonalRib
from openglider.utils.table import Table


class GliderSpreadsheet(object):
    """
    Tabular representation of a glider for easy manipulation
    """
    def __init__(self, glider2d):
        self.glider2d = glider2d
        self.sheets = collections.OrderedDict([
            ("Geometry", Table()),
            ("Cell Elements", Table()),
            ("Rib Elements", Table()),
            ("Airfoils", Table()),
            ("Balloonings", Table()),
            ("Parametric", Table()),
            ("Lines", Table()),
            ("Data", Table())
        ])


    @classmethod
    def read_ods(cls, filepath):
        data = pyexcel_ods3.get_data(filepath)
        return cls.from_dict(data)

    @classmethod
    def read_xls(cls, filepath):
        data =pyexcel_xls.get_data(filepath)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, dct):
        # unpack sheets:
        pass

    def update(self):
        self.set_geometry()
        self.set_cell_parts()
        self.set_rib_parts()
        #self.set_lines()
        #self.set_airfoils()
        #self.set_balloonings()
        #self.set_parametric()
        #self.set_data()

    def set_geometry(self):
        header = ["Ribs", "Chord", "Le x (m)", "Le y (m)", "Arc", "AOA", "Z-rotation", "Y-rotation", "profile-merge", "ballooning-merge"]
        geometry = [header]
        shape = self.glider2d.shape.get_half_shape()
        arc_angles_rad = self.glider2d.arc.get_cell_angles(self.glider2d.shape.rib_x_values) + [0]
        arc_angles = [0] + [angle*180/math.pi for angle in arc_angles_rad]

        aoa_int = self.glider2d.aoa.interpolation(num=100)
        profile_int = self.glider2d.profile_merge_curve.interpolation(num=100)
        ballooning_int = self.glider2d.ballooning_merge_curve.interpolation(num=100)

        for rib_no, x in enumerate(self.glider2d.shape.rib_x_values):
            chord = shape.chords[rib_no]
            front = shape.front[rib_no]
            x = front[0]
            y = -front[1]
            arc_diff = arc_angles[rib_no+1] - arc_angles[rib_no]

            row = [rib_no+1,
                   float(chord),
                   float(x),
                   float(y),
                   float(arc_diff),
                   float(aoa_int(x)*180/math.pi),
                   0,
                   0,
                   float(profile_int(x)),
                   float(ballooning_int(x))]

            geometry.append(row)

        self.sheets["Geometry"] = geometry

    @staticmethod
    def _get_columns(name, row_num, col_num):
        lst = [["" for i in range(row_num+1)] for j in range(col_num)]
        lst[0][0] = name
        return lst

    def set_cell_parts(self):

        row_num = self.glider2d.shape.half_cell_num
        elems = self.glider2d.elements

        columns = [["Cell No."] + [i+1 for i in range(row_num)]]

        # cuts
        # group by type
        cut_types = {}
        for cut in elems["cuts"]:
            cut_type = cut["type"]
            cut_types.setdefault(cut_type, [[]]*row_num)
            for cell_no in cut["cells"]:
                cut_types[cut_type][cell_no].append(copy.copy(cut))

        for cut_type, cells in cut_types.items():
            while any(len(cell) for cell in cells):
                columns_cut = self._get_columns(cut_type, row_num, 2)

                def find_next(x_last=None, cell_start=0):
                    for i, cuts in enumerate(cells[cell_start:]):
                        for cut in cuts:
                            if cut["left"] == x_last or x_last is None:
                                cuts.remove(cut)
                                return cell_start+i, cut

                res = find_next()

                while res:
                    cell_no, cut = res
                    columns_cut[0][cell_no+1] = cut["left"]
                    columns_cut[1][cell_no+1] = cut["right"]

                    res = find_next(cut["right"], cell_no+1)

                columns += columns_cut

        # Diagonals
        for diagonal in elems["diagonals"]:
            diagonal = copy.copy(diagonal)
            cols = self._get_columns("QR", row_num, 6)

            cells = diagonal.pop("cells")
            _diagonal = DiagonalRib(**diagonal)

            for cell_no in cells:
                # center_left, center_right, width_left, width_right, height_left, height_right

                cols[0][cell_no+1] = _diagonal.center_left
                cols[1][cell_no+1] = _diagonal.center_right
                cols[2][cell_no+1] = _diagonal.width_left
                cols[3][cell_no+1] = _diagonal.width_right
                cols[4][cell_no+1] = _diagonal.left_front[1]
                cols[5][cell_no+1] = _diagonal.right_front[1]

            columns += cols

        # Straps
        for strap in elems["straps"]:
            cols = self._get_columns("VEKTLAENGE", row_num, 2)
            for cell_no in strap["cells"]:
                cols[0][cell_no+1] = strap["left"]
                cols[0][cell_no+1] = strap["right"]

        # Material
        max_parts = max([len(c) for c in elems["materials"]])
        cols = [["MATERIAL"] + ["" for i in range(row_num)] for j in range(max_parts)]

        for cell_no, cell in enumerate(elems["materials"]):
            for part_no, part in enumerate(cell):
                cols[part_no][cell_no+1] = part

        columns += cols

        self.sheets["Cell Elements"] = list(zip(*columns))

    def set_rib_parts(self):

        row_num = self.glider2d.shape.half_cell_num + 1
        elems = self.glider2d.elements
        columns = [["Rib No."] + [i+1 for i in range(row_num)]]

        # holes
        for hole in elems["holes"]:
            hole_cols = self._get_columns("HOLE", row_num, 2)
            for rib_no in hole["ribs"]:
                hole_cols[0][rib_no+1] = hole["pos"]
                hole_cols[1][rib_no+1] = hole["size"]

            columns += hole_cols

        # attachment points
        per_rib = [self.glider2d.lineset.get_upper_nodes(rib_no) for rib_no in range(self.glider2d.shape.half_rib_num)]
        max_points = max([len(p) for p in per_rib])
        header = ["AHP", "", ""] * max_points
        attachment_points = [header]

        for rib_no, nodes in enumerate(per_rib):
            nodes.sort(key=lambda node: node.rib_pos)
            row = ["", "", ""] * max_points
            for node_no, node in enumerate(nodes):
                row[node_no*3] = node.name
                row[node_no*3+1] = node.rib_pos
                row[node_no*3+2] = node.force
            attachment_points.append(row)

        columns += list(zip(*attachment_points))

        # rigidfoils
        rigidfoils = elems.get("rigidfoils", [])
        rigidfoils.sort(key=lambda r: r["start"])
        for rigidfoil in rigidfoils:
            rigid_cols = self._get_columns("RIGIDFOIL", row_num, 3)
            for rib_no in rigidfoil["ribs"]:
                rigid_cols[0][rib_no+1] = rigidfoil["start"]
                rigid_cols[1][rib_no+1] = rigidfoil["end"]
                rigid_cols[2][rib_no+1] = rigidfoil["distance"]

            columns += rigid_cols

        self.sheets["Rib Elements"] = list(zip(*columns))

    def set_lines(self):
        table = self.glider2d.lineset.get_table()
        self.sheets["Lines"] = table

    def set_airfoils(self):
        table = Table()
        for airfoil in self.glider2d.profiles:
            x = [p[0] for p in airfoil]
            y = [p[1] for p in airfoil]

            x.insert(0, airfoil.name)
            y.insert(0, "")

            table.add_columns(x, y)

        self.sheets["Airfoils"] = table

    def set_balloonings(self):
        table = Table()
        for ballooning in self.glider2d.balloonings:
            upper = ballooning.controlpoints[0]
            lower = ballooning.controlpoints[1]

            x = [p[0] for p in upper+lower]
            y = [p[1] for p in upper+lower]

            x.insert(0, ballooning.name or "ballooning")
            y.insert(0, "")

            table.add_columns(x, y)

        self.sheets["Balloonings"] = table

    def _transpose_columns(self, data, name):
        x = [p[0] for p in data]
        y = [p[1] for p in data]
        x.insert(0, name)
        y.insert(0, "")

        return x, y

    def set_parametric(self):
        table = Table()

        table.add_columns(*self._transpose_columns(self.glider2d.arc.curve, "Arc"))
        table.add_columns(*self._transpose_columns(self.glider2d.shape.front_curve, "Front"))
        table.add_columns(*self._transpose_columns(self.glider2d.shape.back_curve, "Back"))
        table.add_columns(*self._transpose_columns(self.glider2d.shape.rib_distribution, "Dist"))
        table.add_columns(*self._transpose_columns(self.glider2d.aoa, "AOA"))
        table.add_columns(*self._transpose_columns(self.glider2d.profile_merge_curve, "Profile_merge"))
        table.add_columns(*self._transpose_columns(self.glider2d.ballooning_merge_curve, "Ballooning_merge"))

        self.sheets["Parametric"] = table

    def set_data(self):
        data = {
            "SPEED": self.glider2d.speed,
            "GLIDE": self.glider2d.glide,
            "CELLS": self.glider2d.shape.cell_num
        }

        self.sheets["Data"] = data.items()





    def write_ods(self, filepath):
        pyexcel_ods3.save_data(filepath, self.sheets)

