import re
import copy
import logging

import euklid

from openglider.lines.functions import proj_force
from openglider.lines.elements import Node, SagMatrix
from openglider.mesh import Mesh
from openglider.utils.table import Table

logger = logging.getLogger(__name__)

class LineSet(object):
    """
    Set of different lines
    """
    calculate_sag = True
    knots_table = [
        # lower_line_type, upper_line_type, upper_line_count, first_line_correction, last_line_correction
        ["liros.ltc65", "liros.ltc65", 2, 2.0, 2.0]
    ]

    def __init__(self, lines, v_inf=None):
        self.v_inf = euklid.vector.Vector3D(v_inf)
        self.lines = lines or []

        for line in lines:
            line.lineset = self
        
        self.mat = None
        self.glider = None

    def __repr__(self):
        return """
        {}
        Lines: {}
        Length: {}
        """.format(super(LineSet, self).__repr__(),
                   len(self.lines),
                   self.total_length)
        

    @property
    def lowest_lines(self):
        return [line for line in self.lines if line.lower_node.type == 0]

    @property
    def uppermost_lines(self):
        return [line for line in self.lines if line.upper_node.type == 2]

    @property
    def nodes(self):
        nodes = set()
        for line in self.lines:
            nodes.add(line.upper_node)
            nodes.add(line.lower_node)
        return nodes

    def scale(self, factor):
        for p in self.lower_attachment_points:
            p.vec = p.vec * factor
        for line in self.lines:
            if line.target_length:
                line.target_length *= factor
            if line.init_length:
                line.init_length *= factor
            line.force = None
        for node in self.nodes:
            if node.type == 2: # upper att-node
                node.force *= factor ** 2
        self.recalc(update_attachment_points=False)
        return self

    @property
    def attachment_points(self):
        return [n for n in self.nodes if n.type == 2]

    @property
    def lower_attachment_points(self):
        return [n for n in self.nodes if n.type == 0]

    def get_main_attachment_point(self):
        main_attachment_point = None
        for ap in self.lower_attachment_points:
            if ap.name.upper() == "MAIN":
                main_attachment_point = ap

        if main_attachment_point is None:
            raise RuntimeError("No 'main' attachment point")

        return main_attachment_point

    @property
    def floors(self):
        """
        floors: number of line-levels
        """
        def recursive_count_floors(node):
            if node.type == 2:
                return 0

            lines = self.get_upper_connected_lines(node)
            nodes = [line.upper_node for line in lines]
            depths = [recursive_count_floors(node) for node in nodes]
            return max(depths) + 1

        return {n: recursive_count_floors(n) for n in self.lower_attachment_points}

    def get_lines_by_floor(self, target_floor: int=0, node: Node=None, en_style=True):
        """
        starting from node: walk up "target_floor" floors and return all the lines.

        when en_style is True the uppermost lines are added in case there is no such floor
        (see EN 926.1 for details)
        """
        node =  node or self.get_main_attachment_point()
        def recursive_level(node: Node, current_level: int):
            lines = self.get_upper_connected_lines(node)
            nodes = [line.upper_node for line in lines]
            if not lines and en_style:
                return self.get_lower_connected_lines(node)
            elif current_level == target_floor:
                return lines
            else:
                line_list = []
                for line in lines:
                    line_list += recursive_level(line.upper_node, current_level+1)
                return line_list
                    
        return recursive_level(node, 0)

    def get_floor_strength(self, node: Node=None):
        strength_list = []
        node =  node or self.get_main_attachment_point()
        for i in range(self.floors[node]):
            lines = self.get_lines_by_floor(i, node, en_style=True)
            strength = 0
            for line in lines:
                if line.type.min_break_load is None:
                    logger.warning(f"no min_break_load set for {line.type.name}")
                else:
                    strength += line.type.min_break_load


            strength_list.append(strength)
        return strength_list

    def get_mesh(self, numpoints=10, main_lines_only=False):
        if main_lines_only:
            lines = self.get_upper_lines(self.get_main_attachment_point())
        else:
            lines = self.lines
        return sum([line.get_mesh(numpoints) for line in lines], Mesh())

    def get_upper_line_mesh(self, numpoints=1, breaks=False):
        mesh = Mesh()
        for line in self.uppermost_lines:
            if not breaks:
                # TODO: is there a better solution???
                if "BR" in line.upper_node.name:
                    continue
            mesh += line.get_mesh(numpoints)
        return mesh

    def recalc(self, calculate_sag=True, update_attachment_points=True, iterations=5):
        """
        Recalculate Lineset Geometry.
        if LineSet.calculate_sag = True, drag induced sag will be calculated
        :return: self
        """
        # for att in self.lower_attachment_points:
        #     for line in self.get_upper_connected_lines(att):
        #         for node in self.get_upper_influence_nodes(line):
        #             node.get_position()
        # TODO: recalc always for reproducibility

        if iterations > 1:
            for line in self.lines:
                line.force = None

        if update_attachment_points:
            logger.info("get positions")
            for point in self.attachment_points:
                point.get_position()

        self.calculate_sag = calculate_sag
        
        logger.info("calc geo")
        for _i in range(iterations):
            self._calc_geo()
            if self.calculate_sag:
                self._calc_sag()
            else:
                self.calc_forces(self.lowest_lines)
                for line in self.lines:
                    line.sag_par_1 = line.sag_par_2  = None
        return self

    def _calc_geo(self, start=None):
        if start is None:
            start = self.lowest_lines
        for line in start:
            logger.debug(f"upper line: {line.number}")
            if line.upper_node.type == 1:  # no gallery line
                lower_point = line.lower_node.vec
                tangential = self.get_tangential_comp(line, lower_point)
                line.upper_node.vec = lower_point + tangential * line.init_length

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
            vec = line_lower.diff_vector.normalized()
            if line_lower.upper_node.type != 2:  # not a gallery line
                # recursive force-calculation
                # setting the force from top to down
                lines_upper = self.get_upper_connected_lines(upper_node)
                self.calc_forces(lines_upper)

                force = euklid.vector.Vector3D()
                for line in lines_upper:
                    if line.force is None:
                        logger.warning(f"error line force not set: {line}")
                    else:
                        force += line.diff_vector * line.force
                # vec = line_lower.upper_node.vec - line_lower.lower_node.vec
                line_lower.force = force.dot(vec)

            else:
                force = line_lower.upper_node.force
                force_projected = proj_force(force, vec)
                if force_projected is None:
                    logger.error(f"invalid line: {line_lower.name} ({line_lower.type})")
                    line_lower.force = 10
                else:
                    line_lower.force = force_projected

    def get_upper_connected_lines(self, node):
        return [line for line in self.lines if line.lower_node is node]

    def get_upper_lines(self, node):
        """
        recursive upper lines for node
        :param node:
        :return:
        """
        lines = self.get_upper_connected_lines(node)
        for line in lines[:]:  # copy to not mess up the loop
            lines += self.get_upper_lines(line.upper_node)

        return lines

    def get_lower_connected_lines(self, node):
        return [line for line in self.lines if line.upper_node is node]

    def get_connected_lines(self, node):
        return self.get_upper_connected_lines(node) + self.get_lower_connected_lines(node)

    def get_drag(self):
        """
        Get Total drag of the lineset
        :return: Center of Pressure, Drag (1/2*cw*A*v^2)
        """
        drag_total = 0.
        center = euklid.vector.Vector3D()

        for line in self.lines:
            drag_total += line.drag_total
            center += line.get_line_point(0.5) * line.drag_total
        
        center /= drag_total

        return center, drag_total

    def get_weight(self):
        weight = 0
        for line in self.lines:
            weight += line.get_weight()

        return weight


    def get_normalized_drag(self):
        """get the line drag normalized by the velocity ** 2 / 2"""
        return self.get_drag()[1] / self.v_inf.length()**2 * 2

    # -----CALCULATE GEO-----#
    def get_tangential_comp(self, line, pos_vec):
        # upper_lines = self.get_upper_connected_lines(line.upper_node)
        # first we try to use already computed forces
        # and shift the upper node by residual force
        # we have to make sure to not overcompensate the residual force
        if line.has_geo and line.force is not None:
            r = self.get_residual_force(line.upper_node)
            s = line.get_correction_influence(r)

            for con_line in self.get_connected_lines(line.upper_node):
                s += con_line.get_correction_influence(r)
            # the additional factor is needed for stability. A better approach would be to
            # compute the compensation factor s with a system of linear equation. The movement
            # of the upper node has impact on the compensation of residual force
            # of the lower node (and the other way).
            comp = line.diff_vector + r / s * 0.5
            return comp.normalized()

            # if norm(r) == 0:
            #     return line.diff_vector
            # z = r / np.linalg.norm(r)
            # v0 = line.upper_node.vec - line.lower_node.vec
            # s = norm(r)  * (norm(v0) / line.force - v0.dot(z))
            # return normalize(v0 + s * z * 0.1)

        else:
            # if there are no computed forces available, use all the uppermost forces to compute
            # the direction of the line
            tangent = euklid.vector.Vector3D([0,0,0])
            upper_node = self.get_upper_influence_nodes(line)
            for node in upper_node:
                tangent += node.calc_force_infl(pos_vec)

            return tangent.normalized()

    def get_upper_influence_nodes(self, line=None, node=None):
        """
        get the points that have influence on the line and
        are connected to the wing
        """
        if line is not None:
            node = line.upper_node

        if node is None:
            raise ValueError("Must either provide a node or line")

        if node.type == 2:
            return [node]
        else:
            upper_lines = self.get_upper_connected_lines(node)
            result = []
            for upper_line in upper_lines:
                result += self.get_upper_influence_nodes(line=upper_line)
            return result

    def iterate_target_length(self, steps=10, pre_load=50):
        """
        iterative method to satisfy the target length
        """
        self.recalc()
        for i in range(steps):
            for l in self.lines:
                if l.target_length is not None:
                    diff = l.get_stretched_length(pre_load) - l.target_length
                    l.init_length -= diff
                    #l.init_length = l.target_length * l.init_length / l.get_stretched_length(pre_load)
            self.recalc(update_attachment_points=False)

    def _set_line_indices(self):
        for i, line in enumerate(self.lines):
            line.number = i

    @property
    def total_length(self):
        length = 0
        for line in self.lines:
            length += line.get_stretched_length()
        return length
    
    def sort_lines(self, lines=None, x_factor=10):
        if lines is None:
            lines = self.lines
        lines_new = lines[:]

        def sort_key(line):
            nodes = self.get_upper_influence_nodes(line)
            y_value = 0
            val_rib_pos = 0
            for node in nodes:
                if hasattr(node, "rib_pos"):
                    val_rib_pos += node.rib_pos
                else:
                    val_rib_pos += 1000*node.vec[0]

                y_value += node.vec[1]

            return (val_rib_pos*x_factor + y_value) / len(nodes)
        
        lines_new.sort(key=sort_key)

        return lines_new


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

        return [(line, self.create_tree(line.upper_node)) for line in self.sort_lines(lines)]

    def _get_lines_table(self, callback, start_node=None):
        line_tree = self.create_tree(start_node=start_node)
        table = Table()

        floors = max(self.floors.values())
        columns_per_line = len(callback(line_tree[0][0]))

        def insert_block(line, upper, row, column):
            values = callback(line)
            column_0 = column-columns_per_line

            for index, value in enumerate(values):
                table[row, column_0+index] = value

            if upper:
                for line, line_upper in upper:
                    row = insert_block(line, line_upper, row, column-columns_per_line)
            else:  # Insert a top node
                name = line.upper_node.name
                if not name:
                    name = "XXX"
                table.set_value(column_0-1, row, name)
                #table.set_value(column+2+floors, row, name)
                row += 1
            return row

        row = 1
        for line, upper in line_tree:
            row = insert_block(line, upper, row, floors*(columns_per_line)+2)

        return table
    
    node_group_rex = re.compile(r"[^A-Za-z]*([A-Za-z]*)[^A-Za-z]*")
    def rename_lines(self):
        floors = max(self.floors.values())

        # get all upper nodes + all connected lines
        upper_nodes = []
        for node in self.attachment_points:
            upper_nodes += self.get_upper_influence_nodes(node=node)
        lines = []
        for node in upper_nodes:
            lines += self.get_lower_connected_lines(node)

        for floor in range(floors):
            
            lines_grouped = {}
            for line in lines:
                # get all line layer chars (A/B/C/D/BR)
                line_groups = set()
                for node in self.get_upper_influence_nodes(line):
                    node_group = self.node_group_rex.match(node.name)
                    if node_group:
                        line_groups.add(node_group.group(1))
                
                line_groups_list = list(line_groups)
                line_groups_list.sort()
                line_group_name = "".join(line_groups_list)

                lines_grouped.setdefault(line_group_name, [])
                lines_grouped[line_group_name].append(line)
            
            for name, group in lines_grouped.items():
                group_sorted = self.sort_lines(group, x_factor=0.1)

                for i, line in enumerate(group_sorted):
                    if floor > 0:
                        line.name = f"{floor}_{name}{i+1}"
                    else:
                        line.name = f"{name}{i+1}"
            
            lines_new = set()
            for line in lines:
                for lower_line in self.get_lower_connected_lines(line.lower_node):
                    lines_new.add(lower_line)
            
            lines = list(lines_new)
        
        return self
    
    def get_line_length(self, line):
        length = line.get_stretched_length()
        # seam correction
        length += line.type.seam_correction
        # loop correction
        lower_lines = self.get_lower_connected_lines(line.lower_node)
        if len(lower_lines) == 0:
            return length
        
        lower_line = lower_lines[0] # Todo: Reinforce
        upper_lines = self.sort_lines(self.get_upper_connected_lines(line.lower_node))

        index = upper_lines.index(line)
        total_lines = len(upper_lines)

        for data in self.knots_table:
            name1 = data[0]
            name2 = data[1]
            count = data[2]
            min_value = data[3]
            max_value = data[4]

            if name1 == lower_line.type.name and name2 == line.type.name and count == total_lines:
                shortening = min_value + index * (max_value-min_value) / (total_lines-1)
                length -= (data[3] + (data[4] - shortening))
                
                return length

        logger.warning(f"no shortening values for: {lower_line.type.name} / {line.type.name} ({total_lines})")



        return length


    def get_table(self):
        length_table = self._get_lines_table(lambda line: [round(self.get_line_length(line)*1000)])
        length_table.name = "lines"
        names_table = self._get_lines_table(lambda line: [line.name, line.type.name, line.color])

        def get_checklength(line, upper_lines):
            line_length = line.get_stretched_length()
            if not len(upper_lines):
                return [
                    line_length
                ]
            else:
                lengths = []
                for upper in upper_lines:
                    lengths += get_checklength(*upper)
                
                return [
                    length + line_length for length in lengths
                ]
        
        checklength_values = []
        for line, upper_line in self.create_tree():
            checklength_values += get_checklength(line, upper_line)
        checklength_table = Table()
        
        for index, length in enumerate(checklength_values):
            checklength_table[index+1, 0] = round(1000*length)

        length_table.append_right(checklength_table)
        length_table.append_right(names_table)

        return length_table

    def get_force_table(self):
        def get_line_force(line):
            percentage = ""

            if line.type.min_break_load:
                percentage = "{}%".format(round(100*line.force/line.type.min_break_load,1))

            return [line.type.name, line.force, percentage]

        return self._get_lines_table(get_line_force)


    def get_table_2(self):
        table = self._get_lines_table(lambda line: [line.name, line.type.name, round(line.get_stretched_length()*1000)])
        table.name = "lines_2"
        return table

    def get_table_sorted_lengths(self):
        table = Table()
        table[0,0] = "Name"
        table[0,0] = "Length [mm]"
        lines = list(self.lines)
        lines.sort(key=lambda line: line.name)
        for i, line in enumerate(lines):
            table[i+1, 0] = line.name
            table[i+1, 1] = line.type.name
            table[i+1, 2] = round(line.get_stretched_length()*1000)
        
        return table

    def get_upper_connected_force(self, node):
        '''
        get the sum of the forces of all upper-connected lines
        '''
        force = euklid.vector.Vector3D()
        for line in self.get_upper_connected_lines(node):
            force += line.force * line.diff_vector
        return force

    def get_residual_force(self, node):
        '''
        compute the residual force in a node to due simplified computation of lines
        '''
        residual_force = euklid.vector.Vector3D()
        upper_lines = self.get_upper_connected_lines(node)
        lower_lines = self.get_lower_connected_lines(node)
        for line in upper_lines:
            residual_force += line.diff_vector * line.force
        for line in lower_lines:
            residual_force -= line.diff_vector * line.force

        return residual_force

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
            'v_inf': self.v_inf
        }

    @classmethod
    def __from_json__(cls, lines, nodes, v_inf):
        for line in lines:
            if isinstance(line.upper_node, int):
                line.upper_node = nodes[line.upper_node]
            if isinstance(line.lower_node, int):
                line.lower_node = nodes[line.lower_node]
        obj = cls(lines, v_inf)
        for line in obj.lines:
            line.lineset = obj
        return obj

    def __getitem__(self, name):
        if isinstance(name, list):
            return [self[n] for n in name]
        for line in self.lines:
            if name == line.name:
                return line
        raise KeyError(name)
