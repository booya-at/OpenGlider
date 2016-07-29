import copy
import math
import numpy
from openglider.airfoil import Profile3D
from openglider.utils.cache import CachedObject, cached_property
from openglider.vector.functions import rotation_3d


class Rib(CachedObject):
    """
    Openglider Rib Class: contains a airfoil, needs a startpoint, angle (arcwide), angle of attack,
        glide-wide rotation and glider ratio.
        optional: name, absolute aoa (bool), startposition
    """
    hole_naming_scheme = "{rib.name}h{}"
    rigid_naming_scheme = "{rib.name}rigid{}"

    hashlist = ('aoa_absolute', 'glide', 'arcang', 'zrot', 'chord', 'pos', 'profile_2d')  # pos

    def __init__(self, profile_2d=None, startpoint=None,
                 chord=1., arcang=0, aoa_absolute=0, zrot=0, glide=1,
                 name="unnamed rib", startpos=0.,
                 rigidfoils=None,
                 holes=None, material_code=None):
        self.startpos = startpos
        # TODO: Startpos > Set Rotation Axis in Percent
        self.name = name
        self.profile_2d = profile_2d
        self.glide = glide
        self.aoa_absolute = aoa_absolute
        self.arcang = arcang
        self.zrot = zrot
        self.pos = startpoint  # or HashedList([0, 0, 0])
        self.chord = chord
        self.holes = holes or []
        self.rigidfoils = rigidfoils or []
        self.material_code = material_code or ""

    def __json__(self):
        return {"profile_2d": self.profile_2d,
                "startpoint": self.pos.tolist(),
                "chord": self.chord,
                "arcang": self.arcang,
                "aoa_absolute": self.aoa_absolute,
                "zrot": self.zrot,
                "glide": self.glide,
                "name": self.name,
                "material_code": self.material_code}

    def align_all(self, coo, scale=True):
        """align 2d coordinates to the 3d pos of the rib"""
        if not isinstance(coo, numpy.ndarray):
            coo = numpy.array(coo)
        if len(coo[0]) != 3:
            # adding z-value
            coo = coo.T
            coo = numpy.array([coo[0], coo[1], numpy.zeros(len(coo[0]))]).T
        #appply rotations matrix and transpose back
        coo = coo.dot(self.rotation_matrix.T)
        if scale:
            coo *= self.chord
        coo += self.pos
        return coo

    def align(self, point, scale=True):
        if len(point) == 2:
            return self.align([point[0], point[1], 0], scale=scale)
        elif len(point) == 3:
            if scale:
                return self.pos + (self.rotation_matrix.dot(point) * self.chord)
            else:
                return self.pos + self.rotation_matrix.dot(point)

        raise ValueError("Can only Align one single 2D or 3D-Point")

    def rename_parts(self):
        for hole_no, hole in enumerate(self.holes):
            hole.name = self.hole_naming_scheme.format(hole_no, rib=self)

        for rigid_no, rigid in enumerate(self.rigidfoils):
            rigid.name = self.rigid_naming_scheme.format(rigid_no, rib=self)

    @property
    def aoa_relative(self):
        return self.aoa_absolute + self.__aoa_diff(self.arcang, self.glide)

    @aoa_relative.setter
    def aoa_relative(self, aoa):
        self.aoa_absolute = aoa - self.__aoa_diff(self.arcang, self.glide)

    @cached_property('profile_3d')
    def normvectors(self):
        return map(lambda x: self.rotation_matrix.dot([x[0], x[1], 0]), self.profile_2d.normvectors)

    @cached_property('arcang', 'glide', 'zrot', 'aoa_absolute')
    def rotation_matrix(self):
        zrot = numpy.arctan(self.arcang) / self.glide * self.zrot
        return rib_rotation(self.aoa_absolute, self.arcang, zrot)

    @cached_property('self')
    def profile_3d(self):
        if self.profile_2d.data is not None:
            prof = self.profile_2d.copy()
            #print(self.pos)
            return Profile3D([self.align(p) for p in prof])
            #return Profile3D(self.align_all(prof))
            # prof.scale(self.chord)
            #return Profile3D([self.align(p, scale=False) for p in prof])
            #return Profile3D([self.align(p) for p in self.profile_2d.data], name="profile3d (rib: {})".format(self.name))
        else:
            raise ValueError("no 2d-profile present fortharib at rib {}".format(
                self.name))

    def point(self, x_value):
        return self.align(self.profile_2d.point(x_value))

    @staticmethod
    def __aoa_diff(arc_angle, glide):
        ##Formula for aoa rel/abs: ArcTan[Cos[alpha]/gleitzahl]-aoa[rad];
        return numpy.arctan(numpy.cos(arc_angle) / glide)

    def mirror(self):
        self.arcang = -self.arcang
        # self.zrot = -self.zrot
        self.pos = numpy.multiply(self.pos, [1, -1., 1])

    def copy(self):
        new = copy.deepcopy(self)
        try:
            new.name += "_copy"
        except TypeError:
            new.name = str(new.name) + "_copy"
        return new

    def is_closed(self):
        return self.profile_2d.has_zero_thickness

def rib_rotation(aoa, arc, zrot):
    """
    Rotation Matrix for Ribs, aoa, arcwide-angle and glidewise angle in radians
    return -> numpy.array
    """
    # Rotate Arcangle, rotate from lying to standing (x-z)
    rot = rotation_3d(-arc + math.pi / 2, [-1, 0, 0])
    axis = rot.dot([0, 0, 1])
    rot = rotation_3d(aoa, axis).dot(rot)
    axis = rot.dot([0, 1, 0])
    rot = rotation_3d(zrot, axis).dot(rot)
    #rot = rotation_3d(-math.pi/2, [0, 0, 1]).dot(rot)

    return rot