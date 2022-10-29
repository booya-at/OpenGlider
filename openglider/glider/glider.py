from __future__ import annotations
import logging

from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import copy
import math
from typing import List
import re
import numpy as np
import euklid

import openglider
from openglider.glider.cell.attachment_point import CellAttachmentPoint
from openglider.glider.rib.attachment_point import AttachmentPoint

from openglider.glider.rib.rib import Rib
from openglider.glider.cell.cell import Cell
from openglider.glider.shape import Shape
from openglider.mesh import Mesh
from openglider.utils import consistent_value
from openglider.utils.distribution import Distribution
from openglider.vector.projection import flatten_list
from openglider.lines.lineset import LineSet
from openglider.lines.node import Node

if TYPE_CHECKING:
    from openglider.glider.cell.panel import Panel

logger = logging.getLogger(__name__)


class Glider(object):
    cell_naming_scheme = "c{cell_no}"
    rib_naming_scheme = "p{rib_no}"

    cells: List[Cell]
    lineset: LineSet

    def __init__(self, cells: Optional[List[Cell]]=None, lineset: LineSet=None):
        self.cells: List[Cell] = cells or []
        self.lineset = lineset or LineSet([])

    def __json__(self) -> Dict[str, Any]:
        new = self.copy()
        ribs = new.ribs[:]
        cells = []
        # de-reference Ribs not to store too much data
        for cell in new.cells:
            cell_dct = cell.__json__()
            cell_dct["rib1"] = ribs.index(cell.rib1)
            cell_dct["rib2"] = ribs.index(cell.rib2)
            cells.append(cell_dct)

        return {"cells": cells,
                "ribs": ribs,
                "lineset": self.lineset
                }

    @classmethod
    def __from_json__(cls, cells: List[Dict[str, Any]], ribs: List[Rib], lineset: LineSet) -> Glider:
        cells_new = []
        for cell in cells:
            cell.update({
                "rib1": ribs[cell["rib1"]],
                "rib2": ribs[cell["rib2"]]
            })

            cells_new.append(Cell(**cell))

        glider = cls(cells_new, lineset=lineset)

        attachment_points = glider.attachment_points
        for line in glider.lineset.lines:
            if line.upper_node.name in attachment_points:
                line.upper_node = attachment_points[line.upper_node.name]
        
        glider.lineset.recalc(calculate_sag= True, glider=glider)

        return glider

    def __repr__(self) -> str:
        return """
        {}
        Area: {}
        Span: {}
        A/R: {}
        Cells: {}
        """.format(super(Glider, self).__repr__(),
                   self.area,
                   self.span,
                   self.aspect_ratio,
                   len(self.cells))

    def rename_parts(self) -> None:
        for rib_no, rib in enumerate(self.ribs):
            k = not self.has_center_cell
            rib.name = self.rib_naming_scheme.format(rib=rib, rib_no=rib_no+k)
            rib.rename_parts()

        for cell_no, cell in enumerate(self.cells):
            cell.name = self.cell_naming_scheme.format(cell=cell, cell_no=cell_no+1)
            cell.rename_parts(cell_no=cell_no)

    def get_panel_groups(self) -> Dict[str, List[Panel]]:
        panels: Dict[str, List["openglider.glider.cell.panel.Panel"]] = {}
        for cell in self.cells:
            for panel in cell.panels:
                material_code = str(panel.material)
                panels.setdefault(material_code, [])
                panels[material_code].append(panel)

        return panels

    def get_mesh(self, midribs: int=0) -> Mesh:
        mesh = Mesh()
        for rib in self.ribs:
            if rib.profile_2d.thickness > 1e-5:
                mesh += rib.get_mesh(filled=True)

        for cell in self.cells:
            for diagonal in cell.diagonals:
                mesh += diagonal.get_mesh(cell)

        mesh += self.lineset.get_mesh()
        mesh += self.get_mesh_panels(num_midribs=midribs)
        mesh += self.get_mesh_hull(midribs)

        return mesh

    def get_mesh_panels(self, num_midribs: int=0) -> Mesh:
        mesh = Mesh(name="panels")
        for cell in self.cells:
            for panel in cell.panels:
                mesh += panel.get_mesh(cell, num_midribs)

        return mesh

    def get_mesh_hull(self, num_midribs: int=0, ballooning: bool=True) -> Mesh:
        ribs = self.return_ribs(num_midribs=num_midribs, ballooning=ballooning)

        num = len(ribs)
        numpoints = len(ribs[0])  # points per rib

        polygons: List[Tuple[Tuple[int, int, int, int], Dict[str, Any]]] = []
        boundary: Mesh.boundary_nodes_type = {
            "ribs": [],
            "trailing_edge": []
        }
        for i in range(num-1):  # because we use i+1 below
            boundary["trailing_edge"].append(i*numpoints)
            if not i % (num_midribs+1):
                boundary["ribs"] += [i*numpoints+k for k in range(numpoints-1)]

            for k in range(numpoints - 1):  # same reason as above
                kplus = (k+1) % (numpoints-1)
                polygons.append(((
                    i * numpoints + k,
                    i * numpoints + kplus,
                    (i + 1) * numpoints + kplus,
                    (i + 1) * numpoints + k
                ), {}))
        
        ribs_flat = [p for rib in ribs for p in rib]

        return Mesh.from_indexed(ribs_flat, {"hull": polygons}, boundary)

    def return_ribs(self, num_midribs: int=0, ballooning: bool=True) -> List[List[euklid.vector.Vector3D]]:
        """
        Get a list of rib-curves
        :param num: number of midribs per cell
        :param ballooning: calculate ballooned cells
        :return: nested list of ribs [[[x,y,z],p2,p3...],rib2,rib3,..]
        """
        num_midribs += 1
        if not self.cells:
            return []
        #will hold all the points
        ribs = []
        for cell in self.cells:
            for y in range(num_midribs):
                ribs.append(cell.midrib(y * 1. / num_midribs, ballooning=ballooning).curve.nodes)
        ribs.append(self.cells[-1].midrib(1.).curve.nodes)
        return ribs

    def apply_mean_ribs(self, num_midribs: int=8) -> None:
        """
        Calculate Mean ribs
        :param num_mean:
        :return:
        """
        ribs = [cell.mean_airfoil(num_midribs) for cell in self.cells]
        if self.has_center_cell:
            ribs.insert(0, ribs[1])
        else:
            ribs.insert(0, ribs[0])

        for i in range(len(self.ribs))[:-1]:
            self.ribs[i].profile_2d = (ribs[i] + ribs[i+1]) * 0.5

    def get_midrib(self, y: float=0.) -> openglider.airfoil.Profile3D:
        k = y % 1
        i = int(y - k)
        if i == len(self.cells) and k == 0:  # Stabi-rib
            i -= 1
            k = 1
        return self.cells[i].midrib(k)

    def get_point(self, y: float=0, x: float=-1) -> euklid.vector.Vector3D:
        """
        Get a point on the glider
        :param y: span-wise argument (0, cell_no)
        :param x: chord-wise argument (-1, 1)
        :return: point
        """
        rib = self.get_midrib(y)
        rib_no = int(y)
        dy = y - rib_no
        if rib_no == len(self.ribs)-1:
            rib_no -= 1
            dy = 1
        left_rib = self.ribs[rib_no]
        right_rib = self.ribs[rib_no+1]

        ik_l = left_rib.profile_2d(x)
        ik_r = right_rib.profile_2d(x)
        ik = ik_l + dy * (ik_r - ik_l)
        return rib[ik]

    def mirror(self, cutmidrib: bool=True) -> None:
        if self.has_center_cell and cutmidrib:  # Cut midrib
            self.cells = self.cells[1:]
        for rib in self.ribs:
            rib.mirror()
        for cell in self.cells:
            cell.mirror(mirror_ribs=False)
        self.cells = self.cells[::-1]

    def copy(self) -> Glider:
        return copy.deepcopy(self)

    def copy_complete(self) -> Glider:
        """Returns a mirrored and combined copy of the glider, ready for export/view"""
        other = self.copy()
        other2 = self.copy()
        other2.mirror()
        other2.cells[-1].rib2 = other.cells[0].rib1
        other2.cells = other2.cells + other.cells

        # lineset
        for rib in other2.ribs:
            for p in rib.attachment_points:
                p.get_position(rib)
        
        for cell in other2.cells:
            for p_cell in cell.attachment_points:
                p_cell.get_position(cell)
        
        for node in [node for node in other2.lineset.nodes]:
            if node.node_type != node.NODE_TYPE.UPPER:
                mirror = euklid.vector.Vector3D([1,-1,1])
                node.position *= mirror
            if all(node.force):
                node.force *= mirror

        other2.lineset.lines += other.lineset.lines
        other2.lineset._set_line_indices()
        other2.lineset.recalc()

        # rename
        return other2

    def scale(self, factor: float) -> None:
        for rib in self.ribs:
            rib.pos *= factor
            rib.chord *= factor
        self.lineset.scale(factor)

    @property
    def shape_simple(self) -> Shape:
        """
        Simple (rectangular) shape representation for spline inputs
        """
        last_pos = euklid.vector.Vector2D([0,0])  # y,z
        front = []
        back = []
        x = 0.
        for rib in self.ribs:
            p1 = euklid.vector.Vector2D([rib.pos[1], rib.pos[2]])

            width = (p1-last_pos).length()
            last_pos = p1

            x += width * (rib.pos[1] > 0)  # x-value
            if x == 0:
                last_pos = euklid.vector.Vector2D([0,0])

            y_front = -rib.pos[0] + rib.chord * rib.startpos
            y_back = -rib.pos[0] + rib.chord * (rib.startpos - 1)
            front.append(euklid.vector.Vector2D([x, y_front]))
            back.append(euklid.vector.Vector2D([x, y_back]))

        return Shape(euklid.vector.PolyLine2D(front), euklid.vector.PolyLine2D(back))

    @property
    def shape_flattened(self) -> Shape:
        """
        Projected Shape of the glider (as it would lie on the ground - flattened)
        """
        front, back = flatten_list(self.get_spanwise(0), self.get_spanwise(1))
        zero = euklid.vector.Vector2D([0,0])

        return Shape(front.rotate(-math.pi/2, zero), back.rotate(-math.pi/2, zero))

    @property
    def ribs(self) -> List[Rib]:
        ribs = []
        for cell in self.cells:
            for rib in cell.ribs:
                if rib not in ribs:
                    ribs.append(rib)
        return ribs

    @property
    def profile_numpoints(self) -> int:
        return consistent_value(self.ribs, 'profile_2d.numpoints')

    @profile_numpoints.setter
    def profile_numpoints(self, numpoints: int) -> None:
        self.profile_x_values = list(Distribution.from_nose_cos_distribution(numpoints, 0.3))

    @property
    def profile_x_values(self) -> List[float]:
        return self.ribs[0].profile_2d.x_values
        # return consistent_value(self.ribs, 'profile_2d.x_values')

    @profile_x_values.setter
    def profile_x_values(self, xvalues: List[float]) -> None:
        for rib in self.ribs:
            rib.profile_2d = rib.profile_2d.set_x_values(xvalues)

    @property
    def span(self) -> float:
        span = sum([cell.span for cell in self.cells])

        if self.has_center_cell:
            return 2 * span - self.cells[0].span
        else:
            return 2 * span

    @span.setter
    def span(self, span: float) -> None:
        faktor = span / self.span
        self.scale(faktor)

    @property
    def trailing_edge_length(self) -> float:
        d = 0.
        for i, cell in enumerate(self.cells):
            ballooning = (cell.ballooning[1] + cell.ballooning[-1])/2
            vector = cell.prof1.get(0) - cell.prof2.get(0)

            diff = vector.length() * (1 + ballooning)

            if i == 0 and self.has_center_cell:
                d += diff
            else:
                d += 2 * diff

        return d

    @property
    def area(self) -> float:
        area = 0.
        if len(self.ribs) == 0:
            return 0
        front = self.get_spanwise(0).nodes
        back = self.get_spanwise(1).nodes
        front[0][1] = 0  # Get only half a midrib, if there is...
        back[0][1] = 0
        for i in range(len(front) - 1):
            area += (front[i] - front[i+1]).cross(back[i+1]-front[i+1]).length()
            area += (back[i] - back[i + 1]).cross(back[i] - front[i]).length()
            # By this we get twice the area of half the glider :)
            # http://en.wikipedia.org/wiki/Triangle#Using_vectors
        return area

    @area.setter
    def area(self, area: float) -> None:
        faktor = area / self.area
        self.scale(math.sqrt(faktor))

    @property
    def projected_area(self) -> float:
        projected_area = 0.
        for i, cell in enumerate(self.cells):
            cell_area = cell.projected_area
            if i == 0 and self.has_center_cell:
                projected_area += cell_area
            else:
                projected_area += 2*cell_area
            
        return projected_area

    @property
    def aspect_ratio(self) -> float:
        return self.span ** 2 / self.area

    @aspect_ratio.setter
    def aspect_ratio(self, aspect_ratio: float) -> None:
        area_backup = self.area
        factor = self.aspect_ratio / aspect_ratio
        for rib in self.ribs:
            rib.chord *= factor
        self.area = area_backup

    def get_spanwise(self, x: float=0.) -> euklid.vector.PolyLine3D:
        """
        Return a list of points for a x_value
        """
        return euklid.vector.PolyLine3D([rib.align_x(x) for rib in self.ribs])

    def get_attachment_point_layers(self) -> Dict[str, euklid.vector.Interpolation]:
        regex = re.compile(r"([a-zA-Z]+)([0-9]+)")
        attachment_point_per_group: Dict[str, List[Tuple[int, float]]] = {}

        for rib_no, rib in enumerate(self.ribs):
            for point in rib.attachment_points:
                if match := regex.match(point.name):
                    layer = match.group(1)
                    attachment_point_per_group.setdefault(layer, [])
                    attachment_point_per_group[layer].append((rib_no, point.rib_pos))
        
        curves = {}
        for name, group in attachment_point_per_group.items():
            group.sort(key=lambda p: p[0])
            group.insert(0, (0, group[0][1]))
            curves[name] = euklid.vector.Interpolation(group)


        return curves

    @property
    def centroid(self) -> float:
        """Return x-value of the centroid of the glider"""
        area = 0.
        p = 0.

        for i, cell in enumerate(self.cells):
            cell_area = cell.area
            if i == 0 and self.has_center_cell:
                p += cell.centroid[0] * cell_area
                area += cell.area
            else:
                p += 2 * cell.centroid[0] * cell_area
                area += 2 * cell.area

        return p / area

    @property
    def attachment_points(self) -> Dict[str, AttachmentPoint | CellAttachmentPoint]:
        points: List[AttachmentPoint | CellAttachmentPoint] = []
        for rib in self.ribs:
            points += rib.attachment_points
        for cell in self.cells:
            points += cell.attachment_points
        
        return {
            p.name: p for p in points
        }

    def get_main_attachment_point(self) -> Node:
        """
        convention: "main" in main-attachment-point-name
        """
        logger.warning(f"deprecated -> use lineset.get_main_attachment_point")
        return self.lineset.get_main_attachment_point()

    @property
    def has_center_cell(self) -> bool:
        return abs(self.ribs[0].pos[1]) > 1.e-5

    @property
    def glide(self) -> float:
        return consistent_value(self.ribs, 'glide')

    @glide.setter
    def glide(self, glide: float) -> None:
        for rib in self.ribs:
            rib.glide = glide

        angle = math.atan(1/glide)
        speed = self.lineset.v_inf.length()
        self.lineset.v_inf = euklid.vector.Vector3D([math.cos(angle), 0, math.sin(angle)]) * speed
