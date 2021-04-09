import numpy as np
import math
import euklid

from openglider.lines import Node
from openglider.vector.polygon import Circle, Ellipse
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
        return self._get_flattened(rib).fix_errors()

    def _get_flattened(self, rib):
        max_segment = 0.005  # 5mm
        profile = rib.profile_2d
        profile_normvectors = profile.normvectors

        start = profile.get_ik(self.start)
        end = profile.get_ik(self.end)

        point_range = []
        last_node = None
        for p in profile.curve.get(start, end):
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

        nodes = [
            (profile.curve.get(ik) - profile_normvectors.get(ik) * self.func(x)) * rib.chord 
            for ik, x in zip(indices, point_range)
            ]

        return euklid.vector.PolyLine2D(nodes)


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
    size_abs = True

    def __init__(self, position, size=0.05, material_code=None):
        self.pos = position
        self.size = size
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
        point_1 = profile.curve.get(start)

        if self.size_abs:
            # reverse scale now
            size = self.size / rib.chord
        else:
            size = self.size
        
        n = profile.normvectors.get(start)

        point_2 = point_1 + n * size  # get outside start point
        circle = Circle.from_center_p2(point_1, point_2).get_sequence()

        cuts = circle.cut(profile.curve)

        cut1 = cuts[0]
        cut2 = cuts[-1]

        return circle.get(cut1[0], cut2[0]) + profile.curve.get(cut2[1], cut1[1])


class CellAttachmentPoint(Node):
    ballooned=False

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
            self.vec = self.cell.midrib(self.cell_pos, ballooning=self.ballooned)[ik]
            
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
    """
    Round holes.
    height is relative to profile height, rotation is from lower point
    """
    def __init__(self, pos, size=0.5, width=1, vertical_shift=0., rotation=0.):
        self.pos = pos
        if isinstance(size, (list, tuple)):
            size = np.array(list(size))
        self.size = size
        self.vertical_shift = vertical_shift
        self.rotation = rotation  # rotation around lower point
        self.width = width

    def get_3d(self, rib, num=20):
        hole = self.get_points(rib, num=num)
        return rib.align_all(set_dimension(hole, 3))

    def get_flattened(self, rib, num=80, scale=True):
        points = self.get_points(rib, num)
        if scale:
            points = points * [rib.chord, rib.chord]

        return points

    def get_points(self, rib, num=80):        
        lower = rib.profile_2d.get(self.pos)
        upper = rib.profile_2d.get(-self.pos)

        diff = upper - lower
        if self.rotation:
            diff = euklid.vector.Rotation2D(self.rotation).apply(diff)
        
        center = lower + diff * (0.5 + self.vertical_shift/2)
        outer_point = center + diff * (self.size/2)

        print(lower, upper, diff)
        print(center, outer_point)

        circle = Ellipse.from_center_p2(center, outer_point, self.width)

        return circle.get_sequence(num)

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

