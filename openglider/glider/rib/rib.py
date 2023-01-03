from __future__ import annotations

from typing import List, Any, Optional, TYPE_CHECKING, Sequence, Tuple
import copy
import math
import numpy as np
import logging

import euklid
import pyfoil

from openglider.airfoil import Profile3D
from openglider.glider.rib.attachment_point import AttachmentPoint
from openglider.glider.rib.crossports import RibHoleBase
from openglider.glider.rib.rigidfoils import RigidFoilBase
from openglider.materials.material import Material
from openglider.utils.cache import cached_function, cached_property
from openglider.mesh import Mesh, triangulate
from openglider.glider.rib.sharknose import Sharknose
from openglider.materials import cloth
from openglider.utils.dataclass import BaseModel, dataclass, Field


if TYPE_CHECKING:
    from openglider.lines.line import Line
    from openglider.glider.glider import  Glider


logger = logging.getLogger(__name__)

@dataclass
class Rib:
    """
    Openglider Rib Class: contains a airfoil, needs a startpoint, angle (arcwide), angle of attack,
        glide-wide rotation and glider ratio.
        optional: name, absolute aoa (bool), startposition
    """
    material: Material | None
    profile_2d: pyfoil.Airfoil
    pos: euklid.vector.Vector3D
    chord: float

    glide: float
    aoa_absolute: float
    name: str = "unnamed rib"
    startpos: float = 0.
    arcang: float = 0.
    zrot: float = 0.
    xrot: float = 0.

    holes: List[RibHoleBase] = Field(default_factory=list)
    rigidfoils: List[RigidFoilBase] = Field(default_factory=list)
    attachment_points: List[AttachmentPoint] = Field(default_factory=list)
    sharknose: Sharknose | None = None

    hole_naming_scheme = "{rib.name}h{}"
    rigid_naming_scheme = "{rib.name}rigid{}"

    def __post_init__(self) -> None:
        self.pos = euklid.vector.Vector3D(self.pos)

    def align_all(self, data: euklid.vector.PolyLine2D, scale: bool=True) -> euklid.vector.PolyLine3D:
        """align 2d coordinates to the 3d pos of the rib"""
        if scale:
            return self.transformation.apply(data)
        else:
            return self.rotation_matrix.apply(data).move(self.pos)

    def align(self, point: euklid.vector.Vector2D, scale: bool=True) -> euklid.vector.Vector3D:
        if scale:
            return self.transformation.apply(point)
        else:
            return self.rotation_matrix.apply(point) + self.pos

    def align_x(self, x_value: float) -> euklid.vector.Vector3D:
        ik = self.profile_2d(x_value)
        return self.profile_3d[ik]

    def rename_parts(self) -> None:
        for hole_no, hole in enumerate(self.holes):
            hole.name = self.hole_naming_scheme.format(hole_no, rib=self)

        for rigid_no, rigid in enumerate(self.rigidfoils):
            rigid.name = self.rigid_naming_scheme.format(rigid_no, rib=self)

    @property
    def aoa_relative(self) -> float:
        return self.aoa_absolute + self._aoa_diff(self.arcang, self.glide)

    @aoa_relative.setter
    def aoa_relative(self, aoa: float) -> None:
        self.aoa_absolute = aoa - self._aoa_diff(self.arcang, self.glide)

    @cached_property('profile_3d')
    def normvectors(self) -> List[euklid.vector.Vector3D]:
        return [self.rotation_matrix.apply(p) for p in self.profile_2d.normvectors.nodes]

    @cached_property('arcang', 'glide', 'zrot', 'xrot', 'aoa_absolute')
    def rotation_matrix(self) -> euklid.vector.Transformation:
        zrot = np.arctan(self.arcang) / self.glide * self.zrot
        return rib_rotation(self.aoa_absolute, self.arcang, zrot, self.xrot)

    @cached_property('arcang', 'glide', 'zrot', 'xrot', 'aoa_absolute', 'chord', 'pos')
    def transformation(self) -> euklid.vector.Transformation:
        zrot = np.arctan(self.arcang) / self.glide * self.zrot
        return rib_transformation(self.aoa_absolute, self.arcang, zrot, self.xrot, self.chord, self.pos)

    @cached_property('self')
    def profile_3d(self) -> Profile3D:
        return self.get_profile_3d()
    
    @cached_function("self")
    def get_profile_3d(self, x_values: List[float]=None) -> Profile3D:
        hull = self.get_hull()

        if x_values is not None:
            hull = hull.set_x_values(x_values)

        return Profile3D(self.align_all(hull.curve))

    def point(self, x_value: float) -> euklid.vector.Vector3D:
        return self.align(self.profile_2d.profilepoint(x_value))

    @staticmethod
    def _aoa_diff(arc_angle: float, glide: float) -> float:
        ##Formula for aoa rel/abs: ArcTan[Cos[alpha]/gleitzahl]-aoa[rad];
        return np.arctan(np.cos(arc_angle) / glide)

    def mirror(self) -> None:
        self.arcang *= -1.
        self.xrot *= -1.
        # self.zrot = -self.zrot
        self.pos = self.pos * euklid.vector.Vector3D([1, -1, 1])

    def copy(self) -> Rib:
        new = copy.deepcopy(self)
        try:
            new.name += "_copy"
        except TypeError:
            new.name = str(new.name) + "_copy"
        return new

    def is_closed(self) -> bool:
        return self.profile_2d.thickness < 0.01

    def get_hull(self) -> pyfoil.Airfoil:
        """returns the outer contour of the normalized mesh in form
           of a Polyline"""
        if self.sharknose is not None:
            return self.sharknose.get_modified_airfoil(self)

        return self.profile_2d

    @property
    def normalized_normale(self) -> euklid.vector.Vector3D:
        return self.rotation_matrix.apply([0., 0., 1.])

    def get_lines(self, glider: Glider, brake: bool=False) -> List[Line]:
        att = self.attachment_points
        if not brake:
            att = [p for p in att if p.rib_pos < 1]
        
        connected_lines = set()
        for line in glider.lineset.lines:
            if line.upper_node in att:
                connected_lines.add(line)
        return list(connected_lines)

    def get_mesh(self, hole_num: int=10, filled: bool=False, max_area: float=None) -> Mesh:
        if self.is_closed():
            # stabi
            # TODO: return line
            return Mesh.from_indexed([], {}, {})

        vertices = [(p[0], p[1]) for p in self.get_hull().curve.nodes[:-1]]
        boundary = [list(range(len(vertices))) + [0]]
        hole_centers: List[Tuple[float, float]] = []

        if len(self.holes) > 0 and hole_num > 3:
            for hole in self.holes:
                curves = hole.get_curves(self, num=hole_num, scale=False)

                for curve in curves:
                    start_index = len(vertices)
                    hole_vertices = list(curve)[:-1]
                    hole_indices = list(range(len(hole_vertices))) + [0]
                    vertices += hole_vertices
                    boundary.append([start_index + i for i in hole_indices])

                for p in hole.get_centers(self, scale=False):
                    hole_centers.append((p[0], p[1]))

        if not filled:
            segments = []
            for lst in boundary:
                segments += triangulate.Triangulation.get_segments(lst)
            return Mesh.from_indexed(self.align_all(euklid.vector.PolyLine2D(vertices)).nodes, {'rib': [(l, {}) for l in segments]}, {})
        else:
            tri = triangulate.Triangulation(vertices, boundary, hole_centers)
            if max_area is not None:
                tri.meshpy_max_area = max_area
            
            tri.name = self.name
            mesh = tri.triangulate()

            points = self.align_all(euklid.vector.PolyLine2D(mesh.points))
            boundaries = {self.name: list(range(len(mesh.points)))}

            rib_mesh = Mesh.from_indexed(points.nodes, polygons={"ribs": [(tri, {}) for tri in mesh.elements]} , boundaries=boundaries)
            
            for hole in self.holes:
                if hole_mesh := hole.get_mesh(self):
                    rib_mesh += hole_mesh

            return rib_mesh

    @cached_function("self")
    def get_offset_outline(self, margin: float) -> pyfoil.Airfoil:        
        if margin == 0.:
            return self.profile_2d
        else:
            envelope = self.profile_2d.curve.offset(-margin/self.chord, simple=False)
            
            return pyfoil.Airfoil(envelope)

    def get_projection(self, point: euklid.vector.Vector3D) -> float:
        p1 = self.align(euklid.vector.Vector2D([0,0]))
        p2 = self.align(euklid.vector.Vector2D([1,0]))

        d1 = point - p1
        d2 = p2 - p1
        return d1.dot(d2) / d2.dot(d2)

        
    def get_rigidfoils(self) -> List[RigidFoilBase]:
        if self.sharknose is not None:
            return self.sharknose.update_rigidfoils(self)
        
        return self.rigidfoils



def rib_rotation(aoa: float, arc: float, zrot: float, xrot: float=0) -> euklid.vector.Transformation:
    # align upright -> profile is in x/z layer
    rot0 = euklid.vector.Transformation.rotation(np.pi / 2 - xrot, [1, 0, 0])  # type: ignore

    # rotate aoa -> y (rot0.apply([0,0,1]))
    rot1 = euklid.vector.Transformation.rotation(aoa, [0, 1, 0])  # type: ignore

    # rotate arc
    rot2 = euklid.vector.Transformation.rotation(-arc, [1,0,0])  # type: ignore
    axis = (rot1 * rot2).apply([0,0,1])
    rot3 = euklid.vector.Transformation.rotation(-zrot, axis)  # type: ignore
    
    # reverse order
    return rot3 * rot2 * rot1 * rot0


def rib_transformation(aoa: float, arc: float, zrot: float, xrot: float, scale: float, pos: euklid.vector.Vector3D) -> euklid.vector.Transformation:
    scale_transform = euklid.vector.Transformation.scale(scale)  # type: ignore
    #scale = Scale(scale)
    move = euklid.vector.Transformation.translation(pos)  # type: ignore
    #move = Translation(pos)
    rot = rib_rotation(aoa, arc, zrot, xrot)  # type: ignore
    return scale_transform * rot * move
