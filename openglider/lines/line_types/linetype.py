#! /usr/bin/python2
# -*- coding: utf-8; -*-
#
# (c) 2013 booya (http://booya.at)
#
# This file is part of the OpenGlider project.
#
# OpenGlider is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OpenGlider is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenGlider.  If not, see <http://www.gnu.org/licenses/
from typing import Dict
import sys
import logging

import euklid

logging.getLogger(__name__)

class LineType():
    types: Dict[str, "LineType"] = {}

    def __init__(self, name, thickness, stretch_curve, min_break_load=None, weight=None, seam_correction=0, colors=None, cw=1.1):
        """
        Line Type
        Attributes:
            - name
            - cw (usually 1.1)
            - thickness (in mm)
            - stretch curve: [[force [N], stretch_in_%],...]
            - resistance: minimal break strength
            - weight in g/m
        """
        self.name = name
        self.types[name] = self
        self.cw = cw
        self.thickness = thickness / 1000
        if stretch_curve[0][0] != 0:
            stretch_curve.insert(0, [0, 0])
        self.stretch_curve = stretch_curve
        self.stretch_interpolation = euklid.vector.Interpolation(stretch_curve, extrapolate=True)
        self.weight = weight
        self.seam_correction = seam_correction / 1000
        self.colors = colors or []

        self.min_break_load = min_break_load
    
    def __str__(self):
        return f"linetype: {self.name}"
    
    def __repr__(self):
        return str(self)

    def get_similar_lines(self):
        lines = list(self.types.values())
        lines.remove(self)
        lines.sort(key=lambda line: abs(line.thickness - self.thickness))
        
        return lines

    def get_spring_constant(self):
        force, k = self.stretch_interpolation.nodes[-1]
        try:
            result = force / (k / 100)
        except:
            logging.warn(f"invalid stretch for line type: {self.name}")
            return 50000
            
        return result

    def get_stretch_factor(self, force):
        return 1 + self.stretch_interpolation.get_value(force) / 100

    def predict_weight(self):
        t_mm = self.thickness * 1000.
        return 0.134 * t_mm + 0.6859 * t_mm ** 2

    @classmethod
    def get(cls, name):
        try:
            return cls.types[name]
        except KeyError:
            raise KeyError("Line-type {} not found".format(name))
    
    @classmethod
    def _repr_html_(self):
        html = """
            <table>
                <thead>
                    <tr>
                        <td>name</td>
                        <td>thickness</td>
                        <td>stretch_curve</td>
                        <td>spring</td>
                        <td>resistance</td>
                        <td>weight</td>
                        <td>seam correction</td>
                        <td>Colors</td>
                    </tr>
                </thead>
                """
        
        for line_type in self.types.values():
            html += f"""
                <tr>
                    <td>{line_type.name}</td>
                    <td>{line_type.thickness*1000:.02f}</td>
                    <td>{line_type.stretch_curve}</td>
                    <td>{line_type.get_spring_constant() or 0:.0f}</td>
                    <td>{line_type.min_break_load or 0:.02f}</td>
                    <td>{line_type.weight or 0:.02f}</td>
                    <td>{line_type.seam_correction:.04f}</td>
                    <td>{line_type.colors}</td>
                </tr>

                """
        
        return html


# SI UNITS -> thickness [mm], stretch [N, %]

