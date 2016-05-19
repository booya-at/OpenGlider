import numpy
import copy
from openglider.lines import SagMatrix

from openglider.lines.functions import proj_force
from openglider.mesh import Mesh
from openglider.vector.functions import norm, normalize


class LineSet():
    """
    Set of different lines
    TODO:
        -add stretch
    """
    calculate_sag = True

    def __init__(self, lines, v_inf=None):
        self.v_inf = v_inf
        self.lines = lines or []
        for line in lines:
            line.lineset = self
        self.mat = None
        self.glider = None

    @property
    def lowest_lines(self):
        return [line for line in self.lines if line.lower_node.type == 0]

    @property
    def nodes(self):
        nodes = set()
        for line in self.lines:
            nodes.add(line.upper_node)
            nodes.add(line.lower_node)
        return nodes

    @property
    def attachment_points(self):
        return [n for n in self.nodes if n.type == 2]

    @property
    def lower_attachment_points(self):
        return [n for n in self.nodes if n.type == 0]

    def get_mesh(self, numpoints=10):
        for line in self.lines:
            line_points = line.get_line_points(numpoints=numpoints)
            indices = list(range(numpoints))
            boundary = {"line": [0]}
            if line.upper_node.node_type == 2:
                boundary["attachment_point"] = [numpoints]
            else:
                boundary["line"].append(numpoints)

            line_mesh = Mesh(line_points, indices, boundary)

    def recalc(self):
        """
        Recalculate Lineset Geometry.
        if LineSet.calculate_sag = True, drag induced sag will be calculated
        :return: self
        """
        for att in self.lower_attachment_points:
            for line in self.get_upper_connected_lines(att):
                for node in self.get_upper_influence_nodes(line):
                    node.get_position()
        self._calc_geo()
        if self.calculate_sag:
            self._calc_sag()

        return self

    def _calc_geo(self, start=None):
        if start is None:
            start = self.lowest_lines
        for line in start:
            # print(line.number)
            if line.upper_node.type == 1:  # no gallery line
                lower_point = line.lower_node.vec
                tangential = self.get_tangential_comp(line, lower_point)
                line.upper_node.vec = lower_point + tangential * line.target_length

                self._calc_geo(self.get_upper_connected_lines(line.upper_node))

    def _calc_sag(self, start=None):
        if start is None:
            start = self.lowest_lines
        # 0 every line calculates its parameters
        self.mat = SagMatrix(len(self.lines))

        # calculate projections
        for n in self.nodes:
            n.calc_proj_vec(self.v_inf)

        self.calc_forces(start)
        for line in start:
            self._calc_matrix_entries(line)
        # print(self.mat)
        self.mat.solve_system()
        for l in self.lines:
            l.sag_par_1, l.sag_par_2 = self.mat.get_sag_parameters(l.number)

    # -----CALCULATE SAG-----#
    def _calc_matrix_entries(self, line):
        up = self.get_upper_connected_lines(line.upper_node)
        if line.lower_node.type == 0:
            self.mat.insert_type_0_lower(line)
        else:
            lo = self.get_lower_connected_lines(line.lower_node)
            self.mat.insert_type_1_lower(line, lo[0])

        if line.upper_node.type == 1:
            self.mat.insert_type_1_upper(line, up)
        else:
            self.mat.insert_type_2_upper(line)
        for u in up:
            self._calc_matrix_entries(u)

    def calc_forces(self, start_lines):
        for line_lower in start_lines:
            upper_node = line_lower.upper_node
            vec = line_lower.diff_vector
            if line_lower.upper_node.type != 2:  # not a gallery line
                # recursive force-calculation
                lines_upper = self.get_upper_connected_lines(upper_node)
                self.calc_forces(lines_upper)

                force = numpy.zeros(3)
                for line in lines_upper:
                    if line.force is None:
                        print("error line force not set: {}".format(line))
                    else:
                        force += line.force * line.diff_vector
                # vec = line_lower.upper_node.vec - line_lower.lower_node.vec
                line_lower.force = norm(numpy.dot(force, normalize(vec)))

            else:
                force = line_lower.upper_node.force
                line_lower.force = norm(proj_force(force, normalize(vec)))

    def get_upper_connected_lines(self, node):
        return [line for line in self.lines if line.lower_node is node]

    def get_lower_connected_lines(self, node):
        return [line for line in self.lines if line.upper_node is node]

    def get_connected_lines(self, node):
        return self.get_upper_connected_lines(node) + self.get_lower_connected_lines(node)

    def get_drag(self):
        """
        Get Total drag of the lineset
        :return: Center of Pressure, Drag (1/2*cw*A*v^2)
        """
        centers = [line.get_line_point(0.5) for line in self.lines]
        drag = [line.drag_total for line in self.lines]

        center = numpy.array([0, 0, 0])
        drag_total = sum(drag)
        for p, drag in zip(centers, drag):
            center = center + p*drag
        center /= drag_total

        return center, drag_total

    def get_normalized_drag(self):
        """get the line drag normalized by the velocity ** 2 / 2"""
        return self.get_drag()[1] / norm(self.v_inf) ** 2 * 2

    # -----CALCULATE GEO-----#
    def get_tangential_comp(self, line, pos_vec):
        upper_node_nrs = self.get_upper_influence_nodes(line)
        tangent = numpy.array([0., 0., 0.])
        for node in upper_node_nrs:
            tangent += node.calc_force_infl(pos_vec)
        return normalize(tangent)

    def get_upper_influence_nodes(self, line=None):
        """
        get the points that have influence on the line and
        are connected to the wing
        """
        upper_node = line.upper_node
        if upper_node.type == 2:
            return [upper_node]
        else:
            upper_lines = self.get_upper_connected_lines(upper_node)
            result = []
            for upper_line in upper_lines:
                result += self.get_upper_influence_nodes(upper_line)
            return result

    def iterate_target_length(self, steps=10, pre_load=50):
        """
        iterative method to satisfy the target length
        """
        for i in range(steps):
            for l in self.lines:
                if l.target_length is not None:
                    l.target_length = l.target_length * l.target_length / l.get_stretched_length(pre_load)
            #print("------")
            self.recalc()

    def sort_lines(self):
        # ?
        for i, line in enumerate(self.lines):
            line.number = i

    @property
    def total_length(self):
        length = 0
        for line in self.lines:
            length += line.get_stretched_length()
        return length

    def create_tree(self, start_node=None):
        """
        Create a tree of lines
        :return: [(line, [(upper_line1, []),...]),(...)]
        """
        if start_node is None:
            start_node = self.lower_attachment_points
            lines = []
            for node in start_node:
                lines += self.get_upper_connected_lines(node)
        else:
            lines = self.get_upper_connected_lines(start_node)

        def sort_key(line):
            nodes = self.get_upper_influence_nodes(line)
            return sum([100*node.vec[1]+node.vec[0] for node in nodes])/len(nodes)

        lines.sort(key=sort_key)

        return [(line, self.create_tree(line.upper_node)) for line in lines]

    def copy(self):
        return copy.deepcopy(self)

    def __json__(self):
        new = self.copy()
        nodes = list(new.nodes)
        for line in new.lines:
            line.upper_node = nodes.index(line.upper_node)
            line.lower_node = nodes.index(line.lower_node)

        return {
            'lines': new.lines,
            'nodes': nodes,
            'v_inf': self.v_inf.tolist()
        }

    @classmethod
    def __from_json__(cls, lines, nodes, v_inf):
        for line in lines:
            if isinstance(line.upper_node, int):
                line.upper_node = nodes[line.upper_node]
            if isinstance(line.lower_node, int):
                line.lower_node = nodes[line.lower_node]
        obj = cls(lines, v_inf)
        return obj
