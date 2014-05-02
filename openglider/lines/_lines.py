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
# along with OpenGlider.  If not, see <http://www.gnu.org/licenses/>.

from _functions import *
from _elements import Line, Node, LinePar, SagMatrix
from openglider.vector import normalize, norm
import numpy
import openglider.graphics as g


class Lines():

    """
    Notes:
        -join some loops
        -_private functions
    """

    def __init__(self):
        self.calc_par = {}  # Parameters
        self.line_types = {}
        self.nodes = {}
        self.lines = []

    def calc_geo(self, lines):
        for l in lines:
            if l.upper_node.type == 1:
                vec_0 = l.lower_node.vec
                t = self.get_tangential_comp(l, vec_0)
                self.nodes[l.upper_node_nr].vec = vec_0 + t * l.init_length
                conn_lines = self.get_connected_lines(l.upper_node_nr)
                self.calc_geo(conn_lines)

    def calc_sag(self, lines):
        # 0 every line calculates its parameters
        self.mat = SagMatrix(len(self.lines))      # should go to init
        self._calc_projected_nodes()
        self._update_line_points()  # ???
        self._calc_forces(lines)
        for l in self.lines:
            l._calc_pressure(self.calc_par['SPEED'])
            l._calc_length()
            l._calc_ortho_length()
            l._calc_ortho_force()
        self.start_lines = self.get_lowest_lines()
        for line in self.start_lines:
            self._calc_matrix_entries(line)
        self.mat.solve_system()
        for l in self.lines:
            l.sag_par_1, l.sag_par_2 = self.mat.get_sag_par(l.number)

    def calc_stretch(self):
        pass

    # -----CALCULATE SAG-----#
    def _calc_matrix_entries(self, line):
        up = self._get_upper_conected_lines(line.upper_node_nr)
        if line.lower_node.type == 0:
            self.mat.insert_type_0_lower(line)
        else:
            lo = self._get_lower_connected_line(line.lower_node_nr)
            self.mat.insert_type_1_lower(line, lo)
        if line.upper_node.type == 1:
            self.mat.insert_type_1_upper(line, up)
        else:
            self.mat.insert_type_2_upper(line)
        for u in up:
            self._calc_matrix_entries(u)

    def _calc_forces(self, lowest_lines):
        for lo in lowest_lines:
            if lo.upper_node.type != 2:
                lu = self._get_upper_conected_lines(lo.upper_node.number)
                self._calc_forces(lu)
                force = numpy.zeros(3)
                for l in lu:
                    if l.force is None:
                        print("error line force not set")
                    else:
                        force += l.force * l._get_vec()
                vec = lo.upper_node.vec - lo.lower_node.vec
                lo.force = norm(dot(force, normalize(vec)))

            else:
                force = lo.upper_node.force
                vec = lo.upper_node.vec - lo.lower_node.vec
                lo.force = norm(proj_force(force, normalize(vec)))

    def _calc_length(self):
        """without sag..."""
        for l in self. lines:
            l.calc_length()

    def _get_upper_conected_lines(self, node_nr):
        ret = []
        for l in self.lines:
            if l.lower_node_nr == node_nr:
                ret.append(l)
        return(ret)

    def _get_lower_connected_line(self, node_nr):
        ret = []
        for l in self.lines:
            if l.upper_node_nr == node_nr:
                ret.append(l)
        if len(ret) > 1:
            print("warning!!!, there are too much lower lines")
        return(ret[0])

    def _calc_projected_nodes(self):
        for n in self.nodes.values():
            n.calc_proj_vec(self.calc_par["V_INF"])

    # -----CALCULATE GEO-----#
    def get_tangential_comp(self, line, pos_vec):
        upper_node_nrs = []
        flatten(self.get_upper_influence_node(line), upper_node_nrs)
        tangent = numpy.array([0., 0., 0.])
        for node_nr in upper_node_nrs:
            tangent += self.nodes[node_nr].calc_force_infl(pos_vec)
        return(normalize(tangent))

    def get_upper_influence_node(self, line):
        """get the points that have influence on the line and
        are connected to the wing"""
        upper_node = line.upper_node
        conn_l = self.get_connected_lines(upper_node.number)
        if len(conn_l) == 0:
            return(upper_node.number)
        else:
            return(map(self.get_upper_influence_node, conn_l))

    def get_connected_lines(self, node_number):
        ret = []
        for l in self.lines:
            if l.lower_node_nr == node_number:
                ret.append(l)
        return ret

    def get_lowest_lines(self):
        ret = []
        for l in self.lines:
            n = l.lower_node
            if n.type == 0:
                ret.append(l)
        return(ret)

    # -----IMPORT-----#
    def _update_line_points(self):
        for line in self.lines:
            line.upper_node = self.nodes[line.upper_node_nr]
            line.lower_node = self.nodes[line.lower_node_nr]

    def import_lines(self, path):
        key_dict = {
            "NODES": [8, self.store_nodes],
            "LINES": [5, self.store_lines],
            "LINEPAR": [4, self.store_line_par],
            "CALCPAR": [5, self.store_calc_par]
        }
        import_file(path, key_dict)
        #self.set_line_par()
        self.sort_lines()
        self._update_line_points()

    def store_nodes(self, values):
        n = Node(try_convert(values[0], int))
        n.type = try_convert(values[1], int)
        n.vec = numpy.array(map(lambda x: try_convert(x, float), values[2:5]))
        n.force = numpy.array(
            map(lambda x: try_convert(x, float), values[5:8]))
        self.nodes[n.number] = n

    def store_lines(self, values):
        l = Line(try_convert(values[0], int), values[4])
        l.lower_node_nr = try_convert(values[1], int)
        l.upper_node_nr = try_convert(values[2], int)
        l.init_length = try_convert(values[3], float)
        #l.type = values[4]
        self.lines.append(l)

    def store_line_par(self, values):
        lp = LinePar(values[0])
        lp.cw = try_convert(values[1], float)
        lp.b = try_convert(values[2], float)
        lp.strech = try_convert(values[3], float)
        #self.line_types[lp.type] = lp

    def store_calc_par(self, values):
        self.calc_par["GEOSTEPS"] = try_convert(values[0], int)
        self.calc_par["SAGSTEPS"] = try_convert(values[1], int)
        self.calc_par["ITER"] = try_convert(values[2], int)
        speed = self.calc_par["SPEED"] = try_convert(values[3], float)
        glide = self.calc_par["GLIDE"] = try_convert(values[4], float)
        self.calc_par["V_INF"] = (
            speed * normalize(numpy.array([glide, 0., 1.])))

    def sort_lines(self):
        self.lines.sort(key=(lambda line: line.number))

    # -----VISUALISATION-----#
    def visual_output(self, sag=True, numpoints=10):
        lines = [l.get_line_coords(sag, numpoints, self.calc_par["V_INF"])
                 for l in self.lines]
        g.Graphics3D(map(g.Line, lines))


if __name__ == "__main__":
    lines = Lines()
    lines.import_lines("TEST_INPUT_FILE_1.txt")
    strt = lines.get_lowest_lines()
    lines.calc_geo(strt)
    lines.calc_sag(strt)
    lines.visual_output(numpoints=20)
