from __future__ import annotations
from cmath import isnan

import copy
import dataclasses
import logging
import math
import os
import re
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

import euklid
from openglider.lines.node import Node
from openglider.lines.line import Line
from openglider.lines.elements import SagMatrix
from openglider.lines.functions import proj_force
from openglider.lines.knots import KnotCorrections
from openglider.lines.line_types.linetype import LineType
from openglider.mesh import Mesh
from openglider.utils.table import Table
from openglider.vector.unit import Percentage

if TYPE_CHECKING:
    from openglider.glider.glider import Glider

logger = logging.getLogger(__name__)

@dataclasses.dataclass
class LineLength:
    length: float
    
    seam_correction: float
    loop_correction: float
    knot_correction: float
    manual_correction: float

    def get_checklength(self) -> float:
        length = self.length
        length += self.loop_correction
        length += self.manual_correction

        return length

    def get_length(self) -> float:
        length = self.get_checklength()
        length += self.seam_correction
        length += self.knot_correction

        return length


class LineSet(object):
    """
    Set of different lines
    """
    calculate_sag = True
    knot_corrections = KnotCorrections.read_csv(os.path.join(os.path.dirname(__file__), "knots.csv"))
    mat: SagMatrix
    trim_corrections: Dict[str, float]

    def __init__(self, lines: List[Line], v_inf: euklid.vector.Vector3D=None):
        self._v_inf = v_inf or euklid.vector.Vector3D([0,0,0])
        self.lines = lines or []
        self.trim_corrections = {}


        self.mat = SagMatrix(len(self.lines))
        self.rename_lines()
        

    def __repr__(self) -> str:
        return """
        {}
        Lines: {}
        Length: {}
        """.format(super(LineSet, self).__repr__(),
                   len(self.lines),
                   self.total_length)

    def __json__(self) -> Dict[str, Any]:
        lines = [l.__json__() for l in self.lines]
        nodes = list(self.nodes)
        for line in lines:
            line["upper_node"] = nodes.index(line["upper_node"])
            line["lower_node"] = nodes.index(line["lower_node"])

        return {
            'lines': lines,
            'nodes': nodes,
            'v_inf': self.v_inf
        }

    @classmethod
    def __from_json__(cls, lines: List[Dict[str, Any]], nodes: List[Node], v_inf: euklid.vector.Vector3D) -> LineSet:
        lines_new = []
        for line in lines:
            if isinstance(line["upper_node"], int):
                line["upper_node"] = nodes[line["upper_node"]]
            if isinstance(line["lower_node"], int):
                line["lower_node"] = nodes[line["lower_node"]]
            
            lines_new.append(Line.__from_json__(**line))
        
        v_inf = euklid.vector.Vector3D(v_inf)
        obj = cls(lines_new, v_inf)
        obj.recalc()
        return obj

    @property
    def v_inf(self) -> euklid.vector.Vector3D:
        return self._v_inf
    
    @v_inf.setter
    def v_inf(self, v_inf: euklid.vector.Vector3D) -> None:
        self._v_inf = euklid.vector.Vector3D(v_inf)
        for line in self.lines:
            line.v_inf = self._v_inf

    @property
    def lowest_lines(self) -> List[Line]:
        return [line for line in self.lines if line.lower_node.node_type == Node.NODE_TYPE.LOWER]

    @property
    def uppermost_lines(self) -> List[Line]:
        return [line for line in self.lines if line.upper_node.node_type == Node.NODE_TYPE.UPPER]

    @property
    def nodes(self) -> List[Node]:
        nodes = set()
        for line in self.lines:
            nodes.add(line.upper_node)
            nodes.add(line.lower_node)
        return list(nodes)

    def scale(self, factor: float) -> LineSet:
        for p in self.lower_attachment_points:
            p.position = p.position * factor
        for line in self.lines:
            if line.target_length:
                line.target_length *= factor
            if line.init_length:
                line.init_length *= factor
            line.force = None
        for node in self.nodes:
            if node.node_type == Node.NODE_TYPE.UPPER:
                node.force *= factor ** 2
        self.recalc()
        return self

    @property
    def attachment_points(self) -> List[Node]:
        return [n for n in self.nodes if n.node_type == Node.NODE_TYPE.UPPER]

    @property
    def lower_attachment_points(self) -> List[Node]:
        return [n for n in self.nodes if n.node_type == Node.NODE_TYPE.LOWER]

    def get_main_attachment_point(self) -> Node:
        main_attachment_point = None
        for ap in self.lower_attachment_points:
            if ap.name.upper() == "MAIN":
                main_attachment_point = ap

        # backwards compat
        if main_attachment_point is None:
            for ap in self.lower_attachment_points:
                if ap.name.upper() == "0":
                    main_attachment_point = ap
            
            if main_attachment_point is None:
                logger.error("No 'main' attachment point")
                if len(self.lower_attachment_points) < 1:
                    raise ValueError("no attachment points available")
                main_attachment_point = self.lower_attachment_points[0]

        return main_attachment_point

    @property
    def floors(self) -> Dict[Node, int]:
        """
        floors: number of line-levels
        """
        def recursive_count_floors(node: Node) -> int:
            if node.node_type == Node.NODE_TYPE.UPPER:
                return 0

            lines = self.get_upper_connected_lines(node)
            nodes = [line.upper_node for line in lines]
            depths = [recursive_count_floors(node) for node in nodes]
            return max(depths) + 1

        return {n: recursive_count_floors(n) for n in self.lower_attachment_points}

    def get_lines_by_floor(self, target_floor: int=0, node: Node=None, en_style: bool=True) -> List[Line]:
        """
        starting from node: walk up "target_floor" floors and return all the lines.

        when en_style is True the uppermost lines are added in case there is no such floor
        (see EN 926.1 for details)
        """
        node =  node or self.get_main_attachment_point()
        def recursive_level(node: Node, current_level: int) -> List[Line]:
            lines = self.get_upper_connected_lines(node)
            nodes = [line.upper_node for line in lines]
            if not lines and en_style:
                return self.get_lower_connected_lines(node)
            elif current_level == target_floor:
                return lines
            else:
                line_list: List[Line] = []
                for line in lines:
                    line_list += recursive_level(line.upper_node, current_level+1)
                return line_list
                    
        return recursive_level(node, 0)

    def get_floor_strength(self, node: Node=None) -> List[float]:
        strength_list = []
        node =  node or self.get_main_attachment_point()
        for i in range(self.floors[node]):
            lines = self.get_lines_by_floor(i, node, en_style=True)
            strength = 0.
            for line in lines:
                if line.type.min_break_load is None:
                    logger.warning(f"no min_break_load set for {line.type.name}")
                else:
                    strength += line.type.min_break_load


            strength_list.append(strength)
        return strength_list

    def get_mesh(self, numpoints: int=10, main_lines_only: bool=False, line_segment_length: Optional[float]=None) -> Mesh:
        if main_lines_only:
            lines = self.get_upper_lines(self.get_main_attachment_point())
        else:
            lines = self.lines
        return sum([line.get_mesh(numpoints, segment_length=line_segment_length) for line in lines], Mesh())

    def get_upper_line_mesh(self, numpoints: int=1, breaks: bool=False) -> Mesh:
        mesh = Mesh()
        for line in self.uppermost_lines:
            if not breaks:
                # TODO: is there a better solution???
                if "BR" in line.upper_node.name:
                    continue
            mesh += line.get_mesh(numpoints)
        return mesh

    def recalc(self, calculate_sag: bool=True, glider: Optional[Glider]=None, iterations: int=5) -> LineSet:
        """
        Recalculate Lineset Geometry.
        if LineSet.calculate_sag = True, drag induced sag will be calculated
        :return: self
        """
        for line in self.lines:
            line.force = None

        if glider is not None:
            logger.info("get positions")
            for cell in glider.cells:
                for p_cell in cell.attachment_points:
                    p_cell.get_position(cell)
            for rib in glider.ribs:
                for p in rib.attachment_points:
                    p.get_position(rib)

        self.calculate_sag = calculate_sag

        for line in self.lines:
            line.v_inf = self.v_inf
        
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

    def _calc_geo(self, start: Optional[List[Line]]=None) -> None:
        if start is None:
            start_lines = self.lowest_lines
        else:
            start_lines = start

        for line in start_lines:
            if line.upper_node.node_type == Node.NODE_TYPE.KNOT and line.init_length is not None:  # no gallery line
                lower_point = line.lower_node.position
                tangential = self.get_tangential_comp(line, lower_point)

                upper_point = lower_point + tangential * line.init_length

                if math.isnan(upper_point[0]):
                    raise ValueError(f"{line} {lower_point} {tangential} {line.init_length}")
                line.upper_node.position = upper_point

                self._calc_geo(self.get_upper_connected_lines(line.upper_node))

    def _calc_sag(self, start: Optional[List[Line]]=None) -> None:
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
    def _calc_matrix_entries(self, line: Line) -> None:
        up = self.get_upper_connected_lines(line.upper_node)
        if line.lower_node.node_type == Node.NODE_TYPE.LOWER:
            self.mat.insert_type_0_lower(line)
        else:
            lo = self.get_lower_connected_lines(line.lower_node)
            self.mat.insert_type_1_lower(line, lo[0])

        if line.upper_node.node_type == Node.NODE_TYPE.KNOT:
            self.mat.insert_type_1_upper(line, up)
        else:
            self.mat.insert_type_2_upper(line)
        for u in up:
            self._calc_matrix_entries(u)

    def calc_forces(self, start_lines: List[Line]) -> None:
        for line_lower in start_lines:
            upper_node = line_lower.upper_node
            vec = line_lower.diff_vector.normalized()
            if line_lower.upper_node.node_type != Node.NODE_TYPE.UPPER:  # not a gallery line
                # recursive force-calculation
                # setting the force from top to down
                lines_upper = self.get_upper_connected_lines(upper_node)
                self.calc_forces(lines_upper)

                force = euklid.vector.Vector3D()
                for line in lines_upper:
                    if line.force is None:
                        logger.warning(f"error line force not set: {line}")
                    else:
                        line_force = line.diff_vector * line.force
                        if math.isnan(line_force.length()):
                            raise ValueError(f"invalid line force: {line} {line.upper_node} {line.lower_node} {line.force}")
                        force += line_force
                # vec = line_lower.upper_node.vec - line_lower.lower_node.vec

                result = force.dot(vec)

                if math.isnan(result):
                    raise ValueError(f"invalid force: {force} {vec} {line_lower}")
                else:
                    line_lower.force = force.dot(vec)

            else:
                force = line_lower.upper_node.force
                force_projected = proj_force(force, vec)
                if force_projected is None:
                    logger.error(f"invalid line: {line_lower.name} ({line_lower.type}, {force} {vec})")
                    line_lower.force = 10
                else:
                    line_lower.force = force_projected

    def get_upper_connected_lines(self, node: Node) -> List[Line]:
        return [line for line in self.lines if line.lower_node is node]

    def get_upper_lines(self, node: Node) -> List[Line]:
        """
        recursive upper lines for node
        :param node:
        :return:
        """
        lines = self.get_upper_connected_lines(node)
        for line in lines[:]:  # copy to not mess up the loop
            lines += self.get_upper_lines(line.upper_node)

        return lines

    def get_lower_connected_lines(self, node: Node) -> List[Line]:
        return [line for line in self.lines if line.upper_node is node]

    def get_connected_lines(self, node: Node) -> List[Line]:
        return self.get_upper_connected_lines(node) + self.get_lower_connected_lines(node)

    def get_drag(self) -> Tuple[euklid.vector.Vector3D, float]:
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

    def get_weight(self) -> float:
        weight = 0.
        for line in self.lines:
            weight += line.get_weight()

        return weight


    def get_normalized_drag(self) -> float:
        """get the line drag normalized by the velocity ** 2 / 2"""
        return self.get_drag()[1] / self.v_inf.length()**2 * 2

    # -----CALCULATE GEO-----#
    def get_tangential_comp(self, line: Line, pos_vec: euklid.vector.Vector3D) -> euklid.vector.Vector3D:
        # upper_lines = self.get_upper_connected_lines(line.upper_node)
        # first we try to use already computed forces
        # and shift the upper node by residual force
        # we have to make sure to not overcompensate the residual force
        if line.has_geo and line.force is not None:
            r = self.get_residual_force(line.upper_node)

            if r.length() < 1e-10:
                return line.diff_vector

            s = line.get_correction_influence(r)

            for con_line in self.get_connected_lines(line.upper_node):
                s += con_line.get_correction_influence(r)
            # the additional factor is needed for stability. A better approach would be to
            # compute the compensation factor s with a system of linear equation. The movement
            # of the upper node has impact on the compensation of residual force
            # of the lower node (and the other way).
            comp = line.diff_vector + r / s * 0.5
            comp_normalized = comp.normalized()

            if math.isnan(comp_normalized[0]):
                raise ValueError(f"invalid comp_normalized: {comp} {r} {s}")
            
            return comp_normalized

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

    def get_upper_influence_nodes(self, line: Optional[Line]=None, node: Optional[Node]=None) -> List[Node]:
        """
        get the points that have influence on the line and
        are connected to the wing
        """
        if line is not None:
            node = line.upper_node

        if node is None:
            raise ValueError("Must either provide a node or line")

        if node.node_type == Node.NODE_TYPE.UPPER:
            return [node]
        else:
            upper_lines = self.get_upper_connected_lines(node)
            result: List[Node] = []
            for upper_line in upper_lines:
                result += self.get_upper_influence_nodes(line=upper_line)
            return result

    def iterate_target_length(self, steps: int=10, pre_load: float=50) -> None:
        """
        iterative method to satisfy the target length
        """
        # TODO: use pre_load
        self.recalc()
        for _ in range(steps):
            for l in self.lines:
                if l.target_length is not None and l.init_length is not None:
                    diff = self.get_line_length(l).get_length() - l.target_length
                    l.init_length -= diff
            self.recalc()

    def _set_line_indices(self) -> None:
        for i, line in enumerate(self.lines):
            line.number = i

    @property
    def total_length(self) -> float:
        length = 0.
        for line in self.lines:
            length += line.get_stretched_length()
        return length
    
    def get_consumption(self) -> Dict[LineType, float]:
        consumption: Dict[LineType, float] = {}
        for line in self.lines:
            length = self.get_line_length(line).get_length()
            linetype = line.type
            consumption.setdefault(linetype, 0)
            consumption[linetype] += length
        
        return consumption
    
    def sort_lines(self, lines: Optional[List[Line]]=None, x_factor: float=10., by_names: bool=False) -> List[Line]:
        if lines is None:
            lines = self.lines
        lines_new = lines[:]

        if by_names:
            re_name = re.compile(r"^(?P<n>[0-9]+_)?([A-Za-z]+)([0-9]+)")

            matches = {line.name: re_name.match(line.name) for line in lines_new}

            if all(matches.values()):
                line_values = {}
                for name, match in matches.items():
                    if match is None:
                        raise ValueError(f"this is unreachable")
                    floor, layer, index = match.groups()

                    floor_no = 0
                    if floor:
                        floor_no = int(floor[:-1]) # strip "_"

                    layer_no = sum([ord(l) for l in layer.lower()]) / len(layer)

                    line_values[name] = (layer_no, floor_no, int(index))

                lines_new.sort(key=lambda line: line_values[line.name])

                return lines_new

        def sort_key(line: Line) -> float:
            nodes = self.get_upper_influence_nodes(line)
            y_value = 0.
            val_rib_pos = 0.
            for node in nodes:
                position: Percentage | None = getattr(node, "rib_pos", None)
                if position is not None:
                    val_rib_pos += position.si
                else:
                    val_rib_pos += 1000.*node.position[0]

                y_value += node.position[1]

            return (val_rib_pos*x_factor + y_value) / len(nodes)
        
        lines_new.sort(key=sort_key)

        return lines_new


    def create_tree(self, start_nodes: Optional[List[Node]]=None) -> Any:
        """
        Create a tree of lines
        :return: [(line, [(upper_line1, []),...]),(...)]
        """
        # TODO: REMOVE
        if start_nodes is None:
            start_nodes = self.lower_attachment_points

        lines = []
        for node in start_nodes:
            lines += self.get_upper_connected_lines(node)

        return [(line, self.create_tree([line.upper_node])) for line in self.sort_lines(lines, by_names=True)]

    def _get_lines_table(self, callback: Callable[[Line], List[str]], start_nodes: Optional[List[Node]]=None, insert_node_names: bool=True) -> Table:
        line_tree = self.create_tree(start_nodes=start_nodes)
        table = Table()

        floors = max(self.floors.values(), default=0)
        columns_per_line = len(callback(line_tree[0][0]))

        def insert_block(line: Line, upper: List[Any], row: int, column: int) -> int:
            values = callback(line)
            column_0 = column-columns_per_line

            for index, value in enumerate(values):
                table[row, column_0+index] = value

            if upper:
                for line, line_upper in upper:
                    row = insert_block(line, line_upper, row, column-columns_per_line)
            else:
                if insert_node_names:  # Insert a top node
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
    
    def get_input_table(self) -> Table:
        line_tree = self.create_tree()
        table = Table()

        def insert_block(line: Line, upper: Any, row: int, column: int) -> int:
            if column == 0:
                table.set_value(0, row, line.lower_node.name)
                column += 1

            if upper:
                table.set_value(column, row, line.target_length)
                table.set_value(column+1, row, line.type.name)
                for line, line_upper in upper:
                    row = insert_block(line, line_upper, row, column+2)
            else:
                table.set_value(column, row, line.upper_node.name)
                table.set_value(column+1, row, line.type.name)
                row += 1

            return row

        row = 0
        for line, upper_lines in line_tree:
            row = insert_block(line, upper_lines, row, 0)
        
        return table
    
    node_group_rex = re.compile(r"[^A-Za-z]*([A-Za-z]*)[^A-Za-z]*")

    def rename_lines(self) -> LineSet:
        floors = max(self.floors.values(), default=0)

        # get all upper nodes + all connected lines
        upper_nodes = []
        for node in self.attachment_points:
            upper_nodes += self.get_upper_influence_nodes(node=node)
        lines = []
        for node in upper_nodes:
            lines += self.get_lower_connected_lines(node)

        for floor in range(floors):
            
            lines_grouped: Dict[str, List[Line]] = {}
            for line in lines:
                # get all line layer chars (A/B/C/D/BR)
                line_groups = set()
                for node in self.get_upper_influence_nodes(line):
                    if node.name:
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
                    line.name = f"{floor+1}_{name}{i+1}"
            
            lines_new = set()
            for line in lines:
                for lower_line in self.get_lower_connected_lines(line.lower_node):
                    lines_new.add(lower_line)
            
            lines = list(lines_new)
        
        for line in self.lines:
            if line.upper_node.node_type != Node.NODE_TYPE.UPPER:
                line.upper_node.name = line.name
        
        return self
    
    def get_line_length(self, line: Line, with_sag: bool=True) -> LineLength:
        loop_correction = 0.
        # reduce by canopy-loop length / brake offset
        if len(self.get_upper_connected_lines(line.upper_node)) == 0:
            offset = getattr(line.upper_node, "offset")
            if offset:
                loop_correction += float(offset)

        # get knot correction
        knot_correction = 0.
        lower_lines = self.get_lower_connected_lines(line.lower_node)

        if len(lower_lines) > 0:
            lower_line = lower_lines[0] # Todo: Reinforce
            upper_lines = self.sort_lines(self.get_upper_connected_lines(line.lower_node), by_names=True)

            line_no = upper_lines.index(line)
            total_lines = len(upper_lines)

            knot_correction = self.knot_corrections.get(lower_line.type, line.type, total_lines)[line_no]


        return LineLength(
            line.get_stretched_length(sag=with_sag),
            line.type.seam_correction,
            loop_correction,
            knot_correction,
            self.trim_corrections.get(line.name, 0)
        )
    
    def get_checklength(self, node: Node, with_sag: bool=True) -> float:
        length = 0.
        last_node = node
        while lines := self.get_lower_connected_lines(last_node):
            if len(lines) != 1:
                raise ValueError(f"more than one line connected!")
            line_length = self.get_line_length(lines[0], with_sag)

            length += line_length.get_checklength()
            
            last_node = lines[0].lower_node
        
        return length

    def get_table(self) -> Table:
        length_table = self._get_lines_table(lambda line: [f"{self.get_line_length(line).get_length()*1000:.0f}"])
        #length_table = self._get_lines_table(lambda line: [round(line.get_stretched_length()*1000)])
        
        length_table.name = "lines"

        line_name_table = self._get_lines_table(lambda line: [line.name], insert_node_names=False)
        line_type_table = self._get_lines_table(lambda line: [f"{line.type.name} ({line.color})"], insert_node_names=False)
        line_color_table = self._get_lines_table(lambda line: [line.color], insert_node_names=False)

        def get_checklength(line: Line, upper_lines: Any) -> List[float]:
            line_length = self.get_line_length(line).get_checklength()
            
            if not len(upper_lines):
                return [line_length]
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
        
        length_table.append_right(line_name_table)
        length_table.append_right(line_type_table)
        length_table.append_right(line_color_table)

        return length_table

    def get_force_table(self) -> Table:
        def get_line_force(line: Line) -> List[str]:
            percentage = ""

            if line.type.min_break_load and line.force:
                percentage = f"{100*line.force/line.type.min_break_load:.1f}"

            return [line.type.name, str(line.force), percentage]

        return self._get_lines_table(get_line_force)


    def get_table_2(self) -> Table:
        table = self._get_lines_table(lambda line: [line.name, f"{line.type.name} ({line.color})", f"{line.get_stretched_length()*1000:.0f}"])
        table.name = "lines_2"
        return table

    def get_table_sorted_lengths(self) -> Table:
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

    def get_upper_connected_force(self, node: Node) -> euklid.vector.Vector3D:
        '''
        get the sum of the forces of all upper-connected lines
        '''
        force = euklid.vector.Vector3D()
        for line in self.get_upper_connected_lines(node):
            if line.force:
                force += line.diff_vector * line.force
        return force

    def get_residual_force(self, node: Node) -> euklid.vector.Vector3D:
        '''
        compute the residual force in a node to due simplified computation of lines
        '''
        residual_force = euklid.vector.Vector3D()
        upper_lines = self.get_upper_connected_lines(node)
        lower_lines = self.get_lower_connected_lines(node)
        for line in upper_lines:
            force = line.force or 0.
            residual_force += line.diff_vector * force
        for line in lower_lines:
            force = line.force or 0.
            residual_force -= line.diff_vector * force

        return residual_force

    def copy(self) -> LineSet:
        return copy.deepcopy(self)

    def __getitem__(self, name: str) -> Line:
        if isinstance(name, list):
            return [self[n] for n in name]
        for line in self.lines:
            if name == line.name:
                return line
        raise KeyError(name)
