from __future__ import division
import copy
import math
import numpy as np
from openglider.airfoil import Profile3D
from openglider.utils.cache import CachedObject, cached_property
from openglider.vector.functions import rotation_3d, set_dimension
from openglider.vector.transformation import Rotation, Scale, Translation
from openglider.mesh import Mesh, triangulate
from openglider.glider.rib.elements import FoilCurve
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
        # self.curves = [FoilCurve()]
        # TODO: add in paramteric way
        self.curves = []

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
                "holes": self.holes,
                "material_code": self.material_code,
                "name": self.name
                }

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
        return map(lambda x: self.rotation_matrix([x[0], x[1], 0]), self.profile_2d.normvectors)

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
        if self.profile_2d.data is not None:
            return Profile3D(self.align_all(self.profile_2d.data))
        else:
            raise ValueError("no 2d-profile present for the rib at rib {}".format(
                self.name))

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

    def get_hull(self, glider=None):
        """returns the outer contour of the normalized mesh in form
           of a Polyline"""
        profile = copy.deepcopy(self.profile_2d)
        return profile

    @property
    def normalized_normale(self):
        return self.rotation_matrix(np.array([0., 0., 1.]))

    @property
    def in_plane_normale(self):
        return self.rotation_matrix(np.array([0., 1., 0.]))

    def get_attachment_points(self, glider, brake=True):
        return glider.get_rib_attachment_points(self, brake=brake)

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

        vertices = list(self.get_hull(glider))[:-1]
        boundary = [list(range(len(vertices))) + [0]]
        hole_centers = []

        if len(self.holes) > 0 and hole_num > 3:
            for nr, hole in enumerate(self.holes):
                start_index = len(vertices)
                hole_vertices = list(hole.get_flattened(self, num=hole_num, scale=False))[:-1]
                hole_indices = list(range(len(hole_vertices))) + [0]
                vertices += hole_vertices
                boundary.append([start_index + i for i in hole_indices])
                hole_centers.append(hole.get_center(self, scale=False).tolist())

        if not filled:
            segments = []
            for lst in boundary:
                segments += triangulate.Triangulation.get_segments(lst)
            return Mesh.from_indexed(self.align_all(vertices), {'rib': segments}, {})
        else:
            tri = triangulate.Triangulation(vertices, boundary, hole_centers)
            if max_area is not None:
                tri.meshpy_max_area = max_area
            mesh = tri.triangulate()

            triangles = list(mesh.elements)
            vertices = self.align_all(mesh.points)

            return Mesh.from_indexed(vertices, polygons={"ribs": triangles} , boundaries={self.name: list(range(len(vertices)))})


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

        # we have to apply this function once for the profile2d
        # this will change the position of the attachmentpoints!
        # therefore it shouldn't be placed int the get_hull function
        if self.single_skin_par['continued_min']: 
            self.apply_continued_min()

    def apply_continued_min(self):
        self.profile_2d.move_nearest_point(self.single_skin_par['continued_min_end'])
        data = self.profile_2d.data
        x, y = data.T
        min_index = y.argmin()
        y_min = y[min_index]
        new_y = []
        for i, xy in enumerate(data):
            if i > min_index and (self.single_skin_par['continued_min_end'] - xy[0]) > -1e-8:
                new_y += [y_min + (xy[0] - data[min_index][0]) * np.tan(self.single_skin_par['continued_min_angle'])]
            else:
                new_y += [xy[1]]
        self.profile_2d.data = np.array([x, new_y]).T

    @classmethod
    def from_rib(cls, rib, single_skin_par):
        json_dict = rib.__json__()
        json_dict["single_skin_par"] = single_skin_par
        single_skin_rib = cls(**json_dict)
        return single_skin_rib

    def __json__(self):
        json_dict = super(SingleSkinRib, self).__json__()
        json_dict["single_skin_par"] = self.single_skin_par
        return json_dict

    def get_hull(self, glider=None):
        '''
        returns a modified profile2d
        '''
        profile = copy.deepcopy(self.profile_2d)
        attach_pts = glider.get_rib_attachment_points(self)
        pos = list(set([att.rib_pos for att in attach_pts] + [1]))

        if len(pos) > 1:
            span_list = []
            pos.sort()
            # computing the bow start and end points (back to front)
            for i, p in enumerate(pos[:-1]):

                # the profile  has a normed chord of 1
                # so we have to normalize the "att_dist" which is the thickness of
                # rib between two bows. normally something like 2cm
                # length of the flat part at the attachment point
                le_gap = self.single_skin_par["att_dist"] / self.chord / 2
                te_gap = self.single_skin_par["att_dist"] / self.chord / 2

                # le_gap is the gap between the FIRST BOW start and the attachment point next
                # to this point. (before)
                if i == 0 and not self.single_skin_par["le_gap"]: 
                    le_gap = 0

                # te_gap is the gap between the LAST BOW end and the trailing edge
                if i == (len(pos) -2) and not self.single_skin_par["te_gap"]:
                    te_gap = 0

                span_list.append([p + le_gap, pos[i + 1] - te_gap])

            for k, sp in enumerate(span_list):
                if self.single_skin_par["double_first"] and k == 0:
                    continue # do not insert points between att for double-first ribs (a-b)

                # first we insert the start and end point of the bow
                profile.insert_point(sp[0])
                profile.insert_point(sp[1])

                # now we remove all points between these two points
                # we have to use a tolerance to not delete the start and end points of the bow.
                # problem: the x-value of a point inserted in a profile can have a slightly different
                # x-value
                profile.remove_points(sp[0], sp[1], tolerance=1e-5)

                # insert sequence of xvalues between start and end. endpoint=False is necessary because 
                # start and end are already inserted.
                for i in np.linspace(sp[0], sp[1], self.single_skin_par["num_points"], endpoint=False):
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
                        if self.single_skin_par["straight_te"] and i == len(span_list) - 1:
                            return straight_line(x, x0, x1)
                        else:
                            return parabola(x, x0, x1, x_max)
                    else:
                        return x
                profile.apply_function(foo)
        return profile


def pseudo_2d_cross(v1, v2):
    return v1[0] * v2[1] - v1[1] * v2[0]


def straight_line(x, x0, x1):
    x_proj = (x - x0).dot(x1 - x0) / norm(x1 - x0)**2
    return x0 + (x1 - x0) * x_proj


def parabola(x, x0, x1, x_max):
    """parabola used for singleskin ribs
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
