from typing import List, Any, Optional, TYPE_CHECKING
import copy
import math
import numpy as np
import logging

import euklid
import pyfoil

from openglider.airfoil import Profile3D
from openglider.utils.cache import CachedObject, cached_function, cached_property
from openglider.mesh import Mesh, triangulate
from openglider.glider.rib.sharknose import Sharknose
from openglider.materials import cloth


if TYPE_CHECKING:
    from openglider.glider.glider import  Glider


logger = logging.getLogger(__name__)

class Rib(CachedObject):
    """
    Openglider Rib Class: contains a airfoil, needs a startpoint, angle (arcwide), angle of attack,
        glide-wide rotation and glider ratio.
        optional: name, absolute aoa (bool), startposition
    """
    sharknose: Optional[Sharknose]


    hole_naming_scheme = "{rib.name}h{}"
    rigid_naming_scheme = "{rib.name}rigid{}"

    hashlist = ['aoa_absolute', 'glide', 'arcang', 'zrot', 'chord', 'pos', 'profile_2d']  # pos

    def __init__(self, profile_2d: pyfoil.Airfoil, startpoint=None,
                 chord=1., arcang=0, aoa_absolute=0, zrot=0, xrot = 0, glide=1,
                 name="unnamed rib", startpos=0.,
                 rigidfoils=None,
                 holes=None, material=None, sharknose=None):
        self.startpos = startpos
        # TODO: Startpos > Set Rotation Axis in Percent
        self.name = name
        self.profile_2d = profile_2d
        self.glide = glide
        self.aoa_absolute = aoa_absolute
        self.arcang = arcang
        self.zrot = zrot
        self.xrot = xrot
        self.pos = euklid.vector.Vector3D(startpoint)  # or HashedList([0, 0, 0])
        self.chord = chord
        self.holes = holes or []
        self.rigidfoils = rigidfoils or []
        self.sharknose = sharknose

        if material is not None:
            if isinstance(material, str):
                material = cloth.get(material)
            self.material = material
            
        # self.curves = [FoilCurve()]
        # TODO: add in paramteric way
        self.curves: List[Any] = []

    def __json__(self):
        return {"profile_2d": self.profile_2d,
                "startpoint": self.pos,
                "chord": self.chord,
                "arcang": self.arcang,
                "aoa_absolute": self.aoa_absolute,
                "zrot": self.zrot,
                "xrot": self.xrot,
                "glide": self.glide,
                "name": self.name,
                "rigidfoils": self.rigidfoils,
                "holes": self.holes,
                "material": str(self.material),
                "name": self.name,
                "sharknose": self.sharknose
                }

    def align_all(self, data, scale=True) -> euklid.vector.PolyLine3D:
        """align 2d coordinates to the 3d pos of the rib"""
        if scale:
            return self.transformation.apply(data)
        else:
            return self.rotation_matrix.apply(data) + self.pos

    def align(self, point, scale=True) -> euklid.vector.Vector3D:
        if scale:
            return self.transformation.apply(point)
        else:
            return self.rotation_matrix.apply(point) + self.pos

    def align_x(self, x_value):
        ik = self.profile_2d(x_value)
        return self.profile_3d[ik]

    def rename_parts(self):
        for hole_no, hole in enumerate(self.holes):
            hole.name = self.hole_naming_scheme.format(hole_no, rib=self)

        for rigid_no, rigid in enumerate(self.rigidfoils):
            rigid.name = self.rigid_naming_scheme.format(rigid_no, rib=self)

    @property
    def aoa_relative(self):
        return self.aoa_absolute + self._aoa_diff(self.arcang, self.glide)

    @aoa_relative.setter
    def aoa_relative(self, aoa):
        self.aoa_absolute = aoa - self._aoa_diff(self.arcang, self.glide)

    @cached_property('profile_3d')
    def normvectors(self):
        return map(lambda x: self.rotation_matrix.apply([x[0], x[1], 0]), self.profile_2d.normvectors)

    @cached_property('arcang', 'glide', 'zrot', 'xrot', 'aoa_absolute')
    def rotation_matrix(self):
        zrot = np.arctan(self.arcang) / self.glide * self.zrot
        return rib_rotation(self.aoa_absolute, self.arcang, zrot, self.xrot)

    @cached_property('arcang', 'glide', 'zrot', 'xrot', 'aoa_absolute', 'chord', 'pos')
    def transformation(self):
        zrot = np.arctan(self.arcang) / self.glide * self.zrot
        return rib_transformation(self.aoa_absolute, self.arcang, zrot, self.xrot, self.chord, self.pos)

    @cached_property('self')
    def profile_3d(self):
        try:
            return self.get_profile_3d()
        except AttributeError:
            if self.hull is not None:
                return self.hull
        
        raise ValueError(f"no hull {self.name}")
    
    @cached_function("self")
    def get_profile_3d(self, glider=None):
        hull = Profile3D(self.align_all(self.get_hull(glider).curve.nodes))
        if glider is not None:
            self.hull = hull
        
        return hull

    def point(self, x_value):
        return self.align(self.profile_2d.profilepoint(x_value))

    @staticmethod
    def _aoa_diff(arc_angle, glide):
        ##Formula for aoa rel/abs: ArcTan[Cos[alpha]/gleitzahl]-aoa[rad];
        return np.arctan(np.cos(arc_angle) / glide)

    def mirror(self):
        self.arcang *= -1.
        self.xrot *= -1.
        # self.zrot = -self.zrot
        self.pos = self.pos * [1, -1, 1]

    def copy(self):
        new = copy.deepcopy(self)
        try:
            new.name += "_copy"
        except TypeError:
            new.name = str(new.name) + "_copy"
        return new

    def is_closed(self):
        return self.profile_2d.thickness < 0.01

    def get_hull(self, glider: "Glider"=None) -> pyfoil.Airfoil:
        """returns the outer contour of the normalized mesh in form
           of a Polyline"""
        if self.sharknose is not None:
            return self.sharknose.get_modified_airfoil(self)

        return self.profile_2d

    @property
    def normalized_normale(self):
        return self.rotation_matrix.apply([0., 0., 1.])

    def get_attachment_points(self, glider: "Glider", brake=True):
        attach_pts = []

        if glider.has_center_cell and glider.ribs.index(self) == 0:
            return glider.ribs[1].get_attachment_points(glider)

        for att in glider.attachment_points:
            if hasattr(att, "rib"):
                if att.rib == self:
                    if brake or att.rib_pos != 1.:
                        attach_pts.append(att)
        return attach_pts

    def get_lines(self, glider, brake=False):
        att = self.get_attachment_points(glider, brake=brake)
        connected_lines = set()
        for line in glider.lineset.lines:
            if line.upper_node in att:
                connected_lines.add(line)
        return list(connected_lines)

    def get_mesh(self, hole_num=10, glider=None, filled=False, max_area=None):
        if self.is_closed():
            # stabi
            # TODO: return line
            return Mesh.from_indexed([], {}, {})

        vertices = list(self.get_hull(glider).curve)[:-1]
        boundary = [list(range(len(vertices))) + [0]]
        hole_centers = []

        if len(self.holes) > 0 and hole_num > 3:
            for hole in self.holes:
                curves = hole.get_flattened(self, num=hole_num, scale=False)

                for curve in curves:
                    start_index = len(vertices)
                    hole_vertices = list(curve)[:-1]
                    hole_indices = list(range(len(hole_vertices))) + [0]
                    vertices += hole_vertices
                    boundary.append([start_index + i for i in hole_indices])

                for p in hole.get_centers(self, scale=False):
                    hole_centers.append(list(p))

        if not filled:
            segments = []
            for lst in boundary:
                segments += triangulate.Triangulation.get_segments(lst)
            return Mesh.from_indexed(self.align_all(vertices), {'rib': segments}, {})
        else:
            tri = triangulate.Triangulation(vertices, boundary, hole_centers)
            if max_area is not None:
                tri.meshpy_max_area = max_area
            
            tri.name = self.name
            mesh = tri.triangulate()

            vertices = self.align_all(mesh.points)
            boundaries = {self.name: list(range(len(mesh.points)))}

            return Mesh.from_indexed(vertices, polygons={"ribs": mesh.elements} , boundaries=boundaries)

    @cached_function("self")
    def get_margin_outline(self, margin: float) -> pyfoil.Airfoil:
        logger.info(f"calculate envelope: {self.name}: {margin}")
        
        if margin == 0.:
            return self.profile_2d
        else:
            envelope = self.profile_2d.curve.offset(-margin/self.chord, simple=False)
            envelope.fix_errors()
            
            return pyfoil.Airfoil(envelope)

        
    def get_rigidfoils(self):
        if self.sharknose is not None:
            return self.sharknose.update_rigidfoils(self)
        
        return self.rigidfoils



def rib_rotation(aoa, arc, zrot, xrot=0):
    rot0 = euklid.vector.Transformation.rotation(np.pi / 2 - xrot, [1, 0, 0])
    rot1 = euklid.vector.Transformation.rotation(aoa, [0, 1, 0])
    rot2 = euklid.vector.Transformation.rotation(-arc, [1,0,0])
    axis = (rot1 * rot2).apply([0,0,1])
    rot3 = euklid.vector.Transformation.rotation(-zrot, axis)
    
    # reverse order
    return rot3 * rot2 * rot1 * rot0


def rib_transformation(aoa, arc, zrot, xrot, scale, pos):
    scale = euklid.vector.Transformation.scale(scale)
    #scale = Scale(scale)
    move = euklid.vector.Transformation.translation(pos)
    #move = Translation(pos)
    rot = rib_rotation(aoa, arc, zrot, xrot)
    return scale * rot * move
