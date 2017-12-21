from __future__ import division
import copy
import math
import numpy as np
from openglider.airfoil import Profile3D
from openglider.utils.cache import CachedObject, cached_property
from openglider.vector.functions import rotation_3d, set_dimension
from openglider.vector.transformation import Rotation, Scale, Translation
from numpy.linalg import norm



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
                 chord=1., arcang=0, aoa_absolute=0, zrot=0, xrot = 0, glide=1,
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
        self.xrot = xrot
        self.pos = np.array(startpoint)  # or HashedList([0, 0, 0])
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
                "xrot": self.xrot,
                "glide": self.glide,
                "name": self.name,
                "rigidfoils": self.rigidfoils,
                "material_code": self.material_code}

    def align_all(self, data):
        """align 2d coordinates to the 3d pos of the rib"""
        return self.transformation.apply(set_dimension(data, 3))

    def align(self, point, scale=True):
        if len(point) == 2:
            return self.align([point[0], point[1], 0.], scale=scale)
        elif len(point) == 3:
            if scale:
                return self.transformation(point)
            else:
                return self.pos + self.rotation_matrix(point)

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
        return map(lambda x: self.rotation_matrix([x[0], x[1], 0]), self.profile_2d.normvectors)

    @cached_property('arcang', 'glide', 'zrot', 'xrot', 'aoa_absolute')
    def rotation_matrix(self):
        zrot = np.arctan(self.arcang) / self.glide * self.zrot
        return rib_rotation(self.aoa_absolute, self.arcang, zrot)

    @cached_property('arcang', 'glide', 'zrot', 'xrot', 'aoa_absolute', 'chord', 'pos')
    def transformation(self):
        zrot = np.arctan(self.arcang) / self.glide * self.zrot
        return rib_transformation(self.aoa_absolute, self.arcang, zrot, self.xrot, self.chord, self.pos)

    @cached_property('self')
    def profile_3d(self):
        if self.profile_2d.data is not None:
            return Profile3D(self.align_all(self.profile_2d.data))
        else:
            raise ValueError("no 2d-profile present for tha rib at rib {}".format(
                self.name))

    def point(self, x_value):
        return self.align(self.profile_2d.point(x_value))

    @staticmethod
    def __aoa_diff(arc_angle, glide):
        ##Formula for aoa rel/abs: ArcTan[Cos[alpha]/gleitzahl]-aoa[rad];
        return np.arctan(np.cos(arc_angle) / glide)

    def mirror(self):
        self.arcang = -self.arcang
        # self.zrot = -self.zrot
        self.pos = np.multiply(self.pos, [1, -1., 1])

    def copy(self):
        new = copy.deepcopy(self)
        try:
            new.name += "_copy"
        except TypeError:
            new.name = str(new.name) + "_copy"
        return new

    def is_closed(self):
        return self.profile_2d.has_zero_thickness

    def getMesh(self, glider=None):
        """returns the outer contour of the normalized mesh in form
           of a Polyline"""
        profile = copy.deepcopy(self.profile_2d)
        return profile


class SingleSkinRib(Rib):
    def __init__(self, profile_2d=None, startpoint=None,
                 chord=1., arcang=0, aoa_absolute=0, zrot=0, xrot=0., glide=1,
                 name="unnamed rib", startpos=0.,
                 rigidfoils=None, holes=None, material_code=None,
                 single_skin_par=None):
        super(SingleSkinRib, self).__init__(profile_2d=profile_2d, 
                                            startpoint=startpoint,
                                            chord=chord,
                                            arcang=arcang,
                                            aoa_absolute=aoa_absolute,
                                            zrot=zrot,
                                            xrot=xrot,
                                            glide=glide,
                                            name=name,
                                            startpos=startpos,
                                            rigidfoils=rigidfoils,
                                            holes=holes,
                                            material_code=material_code)
        self.single_skin_par = single_skin_par or {}

    def auto_holes(self):
        pass

    @classmethod
    def from_rib(cls, rib, single_skin_par):
        json_dict = rib.__json__()
        json_dict["single_skin_par"] = single_skin_par
        return cls(**json_dict)

    def __json__(self):
        json_dict = super(SingleSkinRib, self).__json__()
        json_dict["single_skin_par"] = self.single_skin_par
        return json_dict

    def getMesh(self, glider):
        '''
        returns a modified profile2d
        '''
        profile = copy.deepcopy(self.profile_2d)
        attach_pts = glider.get_rib_attachment_points(self)
        pos = list(set([att.rib_pos for att in attach_pts] + [1]))
        if len(pos) > 1:
            span_list = []
            pos.sort()
            for i, p in enumerate(pos[:-1]):
                le_gap = self.single_skin_par["att_dist"] / self.chord / 2
                te_gap = self.single_skin_par["att_dist"] / self.chord / 2
                if i == 0 and not self.single_skin_par["le_gap"]: 
                    le_gap = 0
                # len(it) - 2 == range(len(it) - 1)[-1]
                if i == (len(pos) -2) and not self.single_skin_par["te_gap"]:
                    te_gap = 0
                span_list.append([p + le_gap, pos[i + 1] - te_gap])
            for sp in span_list:
                # insert points
                for i in np.linspace(sp[0], sp[1], self.single_skin_par["num_points"]):
                    profile.insert_point(i)

            # construct shifting function:
            foo_list = []
            for i, sp in enumerate(span_list):
                # parabola from 3 points
                if self.single_skin_par["double_first"] and i == 0:
                    continue
                x0 = np.array(profile.profilepoint(sp[0]))
                x1 = np.array(profile.profilepoint(sp[1]))
                x_mid = (x0 + x1)[0] / 2
                height = abs(profile.profilepoint(-x_mid)[1] - 
                             profile.profilepoint(x_mid)[1])
                height *= self.single_skin_par["height"] # anything bewtween 0..1
                y_mid = profile.profilepoint(x_mid)[1] + height
                x_max = np.array([norm(x1 - x0) / 2, height])
                def foo(x, upper):
                    if not upper and x[0] > x0[0] and x[0] < x1[0]:
                        return parabola(x, x0, x1, x_max)
                    else:
                        return x
                profile.apply_function(foo)
        return profile



def pseudo_2d_cross(v1, v2):
    return v1[0] * v2[1] - v1[1] * v2[0]

def parabola(x, x0, x1, x_max):
    """paraboly used for singleskin ribs
       x, x0, x1, x_max ... numpy 2d arrays
       xmax = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)"""
    x_proj = (x - x0).dot(x1 - x0) / norm(x1 - x0)**2
    x_proj = (x_proj - 0.5) * 2
    y_proj = -x_proj **2
    x = np.array([x_proj, y_proj]) * x_max
    c = (x1 - x0)[0] / norm(x1 - x0)
    s = (x1 - x0)[1] / norm(x1 - x0)
    rot = np.array([[c, -s], [s, c]])
    null = - x_max
    return rot.dot(x - null) + x0


# def rib_rotation(aoa, arc, zrot):
#     """
#     Rotation Matrix for Ribs, aoa, arcwide-angle and glidewise angle in radians
#     return -> np.array
#     """
#     # Rotate Arcangle, rotate from lying to standing (x-z)
#     rot = rotation_3d(-arc + math.pi / 2, [-1, 0, 0])
#     axis = rot.dot([0, 0, 1])
#     rot = rotation_3d(aoa, axis).dot(rot)
#     axis = rot.dot([0, 1, 0])
#     rot = rotation_3d(zrot, axis).dot(rot)
#     # rot = rotation_3d(-math.pi/2, [0, 0, 1]).dot(rot)

#     return rot

def rib_rotation(aoa, arc, zrot, xrot=0):
    rot0 = Rotation(np.pi / 2 - xrot, [1, 0, 0])
    rot1 = Rotation(aoa, [0, 1, 0])
    rot2 = Rotation(-arc, [1, 0, 0])
    axis = (rot1 * rot2)([0, 0, 1])
    rot3 = Rotation(-zrot, axis)
    return rot0 * rot1 * rot2 * rot3


def rib_transformation(aoa, arc, zrot, xrot, scale, pos):
    scale = Scale(scale)
    move = Translation(pos)
    rot = rib_rotation(aoa, arc, zrot, xrot)
    return scale * rot * move




if __name__ == "__main__":
    np = numpy
    a, b, c = np.array([0,0]), np.array([1,1]), np.array([0.5, 0.3])
    ls = np.array([np.linspace(a[0], b[0], 50), np.linspace(a[1], b[1], 50)]).T
    print(np.array([parabola(i, a, b, c) for i in ls]))