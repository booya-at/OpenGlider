from typing import List, Dict
import copy
import math
from typing import List

import numpy as np
import euklid

import openglider

from openglider.glider.cell.cell import Cell
from openglider.glider.shape import Shape
from openglider.mesh import Mesh
from openglider.utils import consistent_value
from openglider.utils.distribution import Distribution
from openglider.vector.projection import flatten_list
from openglider.lines.lineset import LineSet

class Glider(object):
    cell_naming_scheme = "c{cell_no}"
    rib_naming_scheme = "r{rib_no}"

    def __init__(self, cells=None, lineset: LineSet=None):
        self.cells: List[Cell] = cells or []
        self.lineset = lineset or LineSet([])

    def __json__(self):
        new = self.copy()
        ribs = new.ribs[:]
        # de-reference Ribs not to store too much data
        for cell in new.cells:
            cell.rib1 = ribs.index(cell.rib1)
            cell.rib2 = ribs.index(cell.rib2)

        for att_point in new.lineset.attachment_points:
            if hasattr(att_point, "rib"):
                att_point.rib = ribs.index(att_point.rib)
            if hasattr(att_point, "cell"):
                att_point.cell = new.cells.index(att_point.cell)

        return {"cells": new.cells,
                "ribs": ribs,
                "lineset": new.lineset
                }

    @classmethod
    def __from_json__(cls, cells, ribs, lineset):
        for cell in cells:
            if isinstance(cell.rib1, int):
                cell.rib1 = ribs[cell.rib1]
            if isinstance(cell.rib2, int):
                cell.rib2 = ribs[cell.rib2]

        for att in lineset.attachment_points:
            if hasattr(att, "rib") and isinstance(att.rib, int):
                att.rib = ribs[att.rib]
            if hasattr(att, "cell") and isinstance(att.cell, int):
                att.cell = cells[att.cell]
        return cls(cells, lineset=lineset)

    def __repr__(self):
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

    def replace_ribs(self, new_ribs) -> None:
        replace_dict = {}
        assert(len(new_ribs) == len(self.ribs))
        for i, rib in enumerate(self.ribs):
            replace_dict[rib] = new_ribs[i]
        for cell in self.cells:
            cell.rib1 = replace_dict[cell.rib1]
            cell.rib2 = replace_dict[cell.rib2]
        for att in self.attachment_points:
            att.rib = replace_dict[att.rib]
            att.get_position()
        
        self.lineset.recalc()

    def rename_parts(self) -> None:
        for rib_no, rib in enumerate(self.ribs):
            k = not self.has_center_cell
            rib.name = self.rib_naming_scheme.format(rib=rib, rib_no=rib_no+k)
            rib.rename_parts()

        for cell_no, cell in enumerate(self.cells):
            cell.name = self.cell_naming_scheme.format(cell=cell, cell_no=cell_no+1)
            cell.rename_parts()

    def get_panel_groups(self) -> Dict[str, List["openglider.glider.cell.elements.Panel"]]:
        panels: Dict[str, List["openglider.glider.cell.elements.Panel"]] = {}
        for cell in self.cells:
            for panel in cell.panels:
                material_code = str(panel.material)
                panels.setdefault(material_code, [])
                panels[material_code].append(panel)

        return panels

    def get_mesh(self, midribs=0) -> Mesh:
        mesh = Mesh()
        for rib in self.ribs:
            if not rib.profile_2d.has_zero_thickness:
                mesh += rib.get_mesh(filled=True, glider=self)

        for cell in self.cells:
            for diagonal in cell.diagonals:
                mesh += diagonal.get_mesh(cell)

        mesh += self.lineset.get_mesh()
        mesh += self.get_mesh_panels(num_midribs=midribs)
        mesh += self.get_mesh_hull(midribs)

        return mesh

    def get_mesh_panels(self, num_midribs=0) -> Mesh:
        mesh = Mesh(name="panels")
        for cell in self.cells:
            for panel in cell.panels:
                mesh += panel.get_mesh(cell, num_midribs)

        return mesh

    def get_mesh_hull(self, num_midribs=0, ballooning=True) -> Mesh:
        ribs = self.return_ribs(num=num_midribs, ballooning=ballooning)

        num = len(ribs)
        numpoints = len(ribs[0])  # points per rib

        polygons = []
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
                polygons.append([
                    i * numpoints + k,
                    i * numpoints + kplus,
                    (i + 1) * numpoints + kplus,
                    (i + 1) * numpoints + k
                ])

        return Mesh.from_indexed(np.concatenate(ribs), {"hull": polygons}, boundary)

    def return_ribs(self, num=0, ballooning=True):
        """
        Get a list of rib-curves
        :param num: number of midribs per cell
        :param ballooning: calculate ballooned cells
        :return: nested list of ribs [[[x,y,z],p2,p3...],rib2,rib3,..]
        """
        num += 1
        if not self.cells:
            return []
        #will hold all the points
        ribs = []
        for cell in self.cells:
            for y in range(num):
                ribs.append(cell.midrib(y * 1. / num, ballooning=ballooning).data)
        ribs.append(self.cells[-1].midrib(1.).data)
        return ribs

    def apply_mean_ribs(self, num_mean=8) -> None:
        """
        Calculate Mean ribs
        :param num_mean:
        :return:
        """
        ribs = [cell.mean_airfoil(num_mean) for cell in self.cells]
        if self.has_center_cell:
            ribs.insert(0, ribs[1])
        else:
            ribs.insert(0, ribs[0])

        for i in range(len(self.ribs))[:-1]:
            self.ribs[i].profile_2d = (ribs[i] + ribs[i+1]) * 0.5

    def close_rib(self, rib=-1) -> None:
        self.ribs[rib].profile_2d *= 0.

    def get_midrib(self, y=0) -> openglider.airfoil.Profile3D:
        k = y % 1
        i = int(y - k)
        if i == len(self.cells) and k == 0:  # Stabi-rib
            i -= 1
            k = 1
        return self.cells[i].midrib(k)

    def get_point(self, y=0, x=-1) -> euklid.vector.Vector3D:
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

    def mirror(self, cutmidrib=True) -> None:
        if self.has_center_cell and cutmidrib:  # Cut midrib
            self.cells = self.cells[1:]
        for rib in self.ribs:
            rib.mirror()
        for cell in self.cells:
            cell.mirror(mirror_ribs=False)
        self.cells = self.cells[::-1]

    def copy(self):
        return copy.deepcopy(self)

    def copy_complete(self):
        """Returns a mirrored and combined copy of the glider, ready for export/view"""
        other = self.copy()
        other2 = self.copy()
        other2.mirror()
        other2.cells[-1].rib2 = other.cells[0].rib1
        other2.cells = other2.cells + other.cells

        # lineset
        for p in other2.lineset.attachment_points:
            p.get_position()
        for node in [node for node in other2.lineset.nodes]:
            if node.type != 2:
                node.vec *= [1, -1, 1]
            if all(node.force):
                node.force *= [1, -1, 1]
        other2.lineset.lines += other.lineset.lines
        other2.lineset._set_line_indices()
        other2.lineset.recalc()

        # rename
        return other2

    def scale(self, faktor) -> None:
        for rib in self.ribs:
            rib.pos *= faktor
            rib.chord *= faktor
        self.lineset.scale(faktor)

    @property
    def shape_simple(self) -> Shape:
        """
        Simple (rectangular) shape representation for spline inputs
        """
        last_pos = euklid.vector.Vector2D([0,0])  # y,z
        front = []
        back = []
        x = 0
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

    # delete ?
    @property
    def arc(self):
        return [rib.pos[1:] for rib in self.ribs]

    @property
    def ribs(self):
        ribs = []
        for cell in self.cells:
            for rib in cell.ribs:
                if rib not in ribs:
                    ribs.append(rib)
        return ribs

    @property
    def profile_numpoints(self):
        return consistent_value(self.ribs, 'profile_2d.numpoints')

    @profile_numpoints.setter
    def profile_numpoints(self, numpoints):
        self.profile_x_values = Distribution.from_nose_cos_distribution(numpoints, 0.3)

    @property
    def profile_x_values(self):
        return self.ribs[0].profile_2d.x_values
        # return consistent_value(self.ribs, 'profile_2d.x_values')

    @profile_x_values.setter
    def profile_x_values(self, xvalues):
        for rib in self.ribs:
            rib.profile_2d = rib.profile_2d.set_x_values(xvalues)

    @property
    def span(self):
        span = sum([cell.span for cell in self.cells])

        if self.has_center_cell:
            return 2 * span - self.cells[0].span
        else:
            return 2 * span

    @span.setter
    def span(self, span):
        faktor = span / self.span
        self.scale(faktor)

    @property
    def trailing_edge_length(self):
        d = 0
        for i, cell in enumerate(self.cells):
            ballooning = (cell.ballooning[1] + cell.ballooning[-1])/2
            vektor = cell.prof1.point(-1) - cell.prof2.point(-1)

            diff = vektor.length() * (1 + ballooning)

            if i == 0 and self.has_center_cell:
                d += diff
            else:
                d += 2 * diff

        return d

    @property
    def area(self):
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
    def area(self, area):
        faktor = area / self.area
        self.scale(math.sqrt(faktor))

    @property
    def projected_area(self):
        projected_area = 0
        for i, cell in enumerate(self.cells):
            cell_area = cell.projected_area
            if i == 0 and self.has_center_cell:
                projected_area += cell_area
            else:
                projected_area += 2*cell_area
            
        return projected_area

    @property
    def aspect_ratio(self):
        return self.span ** 2 / self.area

    @aspect_ratio.setter
    def aspect_ratio(self, aspect_ratio):
        area_backup = self.area
        factor = self.aspect_ratio / aspect_ratio
        for rib in self.ribs:
            rib.chord *= factor
        self.area = area_backup

    def get_spanwise(self, x=None):
        """
        Return a list of points for a x_value
        """
        if x == 0:
            return euklid.vector.PolyLine3D([rib.pos for rib in self.ribs])  # This is much faster
        else:
            return euklid.vector.PolyLine3D([rib.align([x, 0, 0]) for rib in self.ribs])

    @property
    def centroid(self):
        area = 0
        p = 0

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
    def attachment_points(self):
        points = []
        for line in self.lineset.lowest_lines:
            points += self.lineset.get_upper_influence_nodes(line)
        return points

    def get_rib_attachment_points(self, rib, brake=True, include_mirrored=True):
        attach_pts = []
        if include_mirrored:
            if hasattr(rib, 'mirrored_rib') and rib.mirrored_rib:
                rib = rib.mirrored_rib
        for att in self.attachment_points:
            if hasattr(att, "rib"):
                if att.rib == rib:
                    if not ((not brake) and att.rib_pos == 1.):
                        attach_pts.append(att)
        return attach_pts

    def get_cell_attachment_points(self, cell):
        attach_pts = []
        for att in self.attachment_points:
            if hasattr(att, "cell"):
                if att.cell == cell:
                    attach_pts.append(att)
        return attach_pts

    def get_main_attachment_point(self):
        """
        convention: "main" in main-attachment-point-name
        """
        for att in self.lineset.lower_attachment_points:
            if "main" in att.name:
                return att
        else:
            raise AttributeError("no 'main' attachment-point found.")

    @property
    def has_center_cell(self):
        return abs(self.ribs[0].pos[1]) > 1.e-5

    @property
    def glide(self):
        return consistent_value(self.ribs, 'glide')

    @glide.setter
    def glide(self, glide):
        for rib in self.ribs:
            rib.glide = glide

        angle = math.atan(1/glide)
        speed = self.lineset.v_inf.length()
        self.lineset.v_inf = euklid.vector.Vector3D([math.cos(angle), 0, math.sin(angle)]) * speed
