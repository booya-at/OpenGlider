import numpy as np
import math
import euklid

from openglider.lines import Node
from openglider.vector.polygon import Circle
from openglider.vector.polyline import PolyLine2D
from openglider.vector.functions import set_dimension
from openglider.vector import norm
from openglider.vector.transformation import Rotation, Translation, Scale


class RigidFoil(object):
    def __init__(self, start=-0.1, end=0.1, distance=0.005, circle_radius=0.03):
        self.start = start
        self.end = end
        self.distance = distance
        self.circle_radius = circle_radius
        #self.func = lambda x: distance

    def func(self, pos):
        dsq = None
        if -0.05 <= pos - self.start < self.circle_radius:
            dsq = self.circle_radius**2 - (self.circle_radius + self.start - pos)**2
        if -0.05 <= self.end - pos < self.circle_radius:
            dsq = self.circle_radius**2 - (self.circle_radius + pos - self.end)**2

        if dsq is not None:
            dsq = max(dsq, 0)
            return self.distance + (self.circle_radius - np.sqrt(dsq)) * 0.35
        return self.distance

    def __json__(self):
        return {'start': self.start,
                'end': self.end,
                'distance': self.distance}

    def get_3d(self, rib):
        return [rib.align(p, scale=False) for p in self.get_flattened(rib)]

    def get_length(self, rib):
        return self.get_flattened(rib).get_length()

    def get_flattened(self, rib):
        return euklid.vector.PolyLine2D(self._get_flattened(rib)).fix_errors()

    def _get_flattened(self, rib):
        max_segment = 0.005  # 5mm
        profile = rib.profile_2d
        profile_normvectors = euklid.vector.PolyLine2D(profile.normvectors)

        start = profile(self.start)
        end = profile(self.end)

        point_range = []
        last_node = None
        for p in profile[start:end]:
            sign = -1 if p[1] > 0 else +1

            if last_node is not None:
                diff = norm(p - last_node) * rib.chord
                if diff > max_segment:
                    segments = int(math.ceil(diff/max_segment))
                    point_range += list(np.linspace(point_range[-1], sign*p[0], segments))[1:]
                else:
                    point_range.append(sign*p[0])
            else:
                point_range.append(sign*p[0])

            last_node = p

        indices = [profile(x) for x in point_range]

        return [(profile[ik] - profile_normvectors.get(ik) * self.func(x)) * rib.chord for ik, x in zip(indices, point_range)]


class FoilCurve(object):
    def __init__(self, front=0, end=0.17):
        self.front = front
        self.end = end

    def get_flattened(self, rib, numpoints=30):
        curve = [
            [self.end, 0.75],
            [self.end-0.05, 1],
            [self.front, 0],
            [self.end-0.05, -1],
            [self.end, -0.75]
        ]
        profile = rib.profile_2d

        controlpoints = [profile.align(point)*rib.chord for point in curve]

        return euklid.spline.BezierCurve(controlpoints).get_sequence(numpoints)


class GibusArcs(object):
    """
    A Reinforcement, in the shape of an arc, to reinforce attachment points
    """
    def __init__(self, position, size=0.2, material_code=None):
        self.pos = position
        self.size = size
        self.size_abs = False
        self.material_code = material_code or ""

    def __json__(self):
        return {'position': self.pos,
                'size': self.size}

    def get_3d(self, rib, num_points=10):
        # create circle with center on the point
        gib_arc = self.get_flattened(rib, num_points=num_points)
        return [rib.align([p[0], p[1], 0], scale=False) for p in gib_arc]

    def get_flattened(self, rib, num_points=10):
        # get center point
        profile = rib.profile_2d
        start = profile(self.pos)
        point_1 = profile[start]

        if self.size_abs:
            # reverse scale now
            size = self.size / rib.chord
        else:
            size = self.size
        point_2 = profile.profilepoint(self.pos + size)

        gib_arc = [[], []]  # first, second
        circle = Circle(point_1, point_2).get_sequence()[1:]
        #circle = Polygon(edges=num_points)(point_1, point_2)[0][1:] # todo: is_center -> true
        is_second_run = False
        
        for i in range(len(circle)):
            if profile.contains_point(circle[i]) or \
                    (i < len(circle) - 1 and profile.contains_point(circle[i + 1])) or \
                    (i > 1 and profile.contains_point(circle[i - 1])):
                gib_arc[is_second_run].append(circle[i])
            else:
                is_second_run = True

        # Cut first and last
        gib_arc = gib_arc[1] + gib_arc[0]  # [secondlist] + [firstlist]
        start2 = profile.cut(gib_arc[0], gib_arc[1], start)
        stop = profile.cut(gib_arc[-2], gib_arc[-1], start)
        # Append Profile_List
        gib_arc += profile.get(start2.next()[0], stop.next()[0]).tolist()

        return np.array(gib_arc) * rib.chord


class CellAttachmentPoint(Node):
    def __init__(self, cell, name, cell_pos, rib_pos, force=None):
        super(CellAttachmentPoint, self).__init__(node_type=2)
        self.cell = cell
        self.cell_pos = cell_pos
        self.rib_pos = rib_pos
        self.name = name
        self.force = force

    def __repr__(self):
        return "<Attachment point '{}' ({})>".format(self.name, self.rib_pos)

    def __json__(self):
        return {
            "cell": self.cell,
            "cell_pos": self.cell_pos,
            "rib_pos": self.rib_pos,
            "name": self.name,
            "force": self.force
        }

    def get_position(self):
        ik = self.cell.rib1.profile_2d(self.rib_pos)

        if self.rib_pos in (-1, 1):
            self.vec = (self.cell.rib1.profile_3d.get(ik) + self.cell.rib2.profile_3d.get(ik))/2
        else:
            self.vec = self.cell.midrib(self.cell_pos)[ik]
            
        return self.vec

# Node from lines
class AttachmentPoint(Node):
    def __init__(self, rib, name, rib_pos, force=None):
        super(AttachmentPoint, self).__init__(node_type=2)
        self.rib = rib
        self.rib_pos = rib_pos
        self.name = name
        self.force = force

    def __repr__(self):
        return "<Attachment point '{}' ({})>".format(self.name, self.rib_pos)

    def __json__(self):
        return {"rib": self.rib,
                "name": self.name,
                "rib_pos": self.rib_pos,
                "force": self.force}


    def get_position(self):
        self.vec = self.rib.profile_3d[self.rib.profile_2d(self.rib_pos)]
        return self.vec


class RibHole(object):
    def __init__(self, pos, size=0.5, vertical_shift=0., rotation=0.):
        self.pos = pos
        if isinstance(size, (list, tuple)):
            size = np.array(list(size))
        self.size = size
        self.vertical_shift = vertical_shift
        self.rotation = rotation  # rotation about p1

    def get_3d(self, rib, num=20):
        hole = self.get_points(rib, num=num)
        return rib.align_all(set_dimension(hole, 3))

    def get_flattened(self, rib, num=80, scale=True):
        points = self.get_points(rib, num)
        if scale:
            points = points * [rib.chord, rib.chord]

        return points

    def get_points(self, rib, num=80):
        prof = rib.profile_2d
        
        p1 = prof.get(self.pos)
        p2 = prof.get(-self.pos)

        phi = np.linspace(0, np.pi * 2, num + 1)
        points = np.array([np.cos(phi), np.sin(phi)]).T
        #delta = (p2 - p1) / 2 * self.vertical_shift + (p1 + p2) / 2
        move_1 = Translation(p1)
        move_2 = Translation((p2 - p1) * 0.5 * (1 + self.vertical_shift))
        rot = Rotation(self.rotation)
        scale = Scale(np.linalg.norm(p2 - p1) / 2 * self.size)
        points = (scale * move_2 * rot * move_1).apply(points)

        return euklid.vector.PolyLine2D(points.tolist())

    def get_center(self, rib, scale=True):
        prof = rib.profile_2d

        p1 = prof.get(self.pos)
        p2 = prof.get(-self.pos)

        if scale:
            p1 *= rib.chord
            p2 *= rib.chord

        move_1 = Translation(p1)
        move_2 = Translation((p2 - p1) * 0.5 * (1 + self.vertical_shift))
        rot = Rotation(self.rotation)
        return (move_2 * rot * move_1)([0., 0.])

    def __json__(self):
        return {
            "pos": self.pos,
            "size": self.size,
            "vertical_shift": self.vertical_shift,
            "rotation": self.rotation}


class RibSquareHole:
    def __init__(self, start, stop, height):
        pass

    def get_3d(self, rib, num=20):
        hole = self.get_points(rib, num=num)
        return rib.align_all(set_dimension(hole, 3))

    def get_flattened(self, rib, num=80, scale=True):
        points = self.get_points(rib, num).data
        if scale:
            points *= rib.chord
        return euklid.vector.PolyLine2D(points)
        #return Polygon(p1, p2, num=num, scale=self.size, is_center=False)[0]

    def get_points(self, rib, num=80):
        points = []

        return euklid.vector.PolyLine2D(points, name=f"{rib.name}-hole")

    def __json__(self):
        return {
            }



class Mylar(object):
    pass

