from typing import List
import numpy as np
import logging
import math
import euklid

import openglider
from openglider.lines import Node
from openglider.vector.polygon import Circle, Ellipse

logger = logging.getLogger(__name__)

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
                diff = (p - last_node).length() * rib.chord
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

    def get_3d(self, rib: "openglider.glider.rib.Rib", num_points=10) -> euklid.vector.PolyLine3D:
        # create circle with center on the point
        gib_arc = self.get_flattened(rib, num_points=num_points)

        return rib.align_all(gib_arc, scale=False)
        #return [rib.align([p[0], p[1], 0], scale=False) for p in gib_arc]

    def get_flattened(self, rib, num_points=10) -> euklid.vector.PolyLine2D:
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

    def get_position(self) -> euklid.vector.Vector3D:
        ik = self.cell.rib1.profile_2d(self.rib_pos)

        if self.rib_pos in (-1, 1):
            p1 = self.cell.rib1.profile_3d.get(ik)
            p2 = self.cell.rib2.profile_3d.get(ik)
            self.vec = p1 + (p2 - p1)*self.cell_pos
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


    def get_position(self) -> euklid.vector.Vector3D:
        # todo: PROFILE3D -> return euklid vector
        self.vec = self.rib.profile_3d[self.rib.profile_2d(self.rib_pos)]
        return self.vec


class RibHole(object):
    """
    Round holes.
    height is relative to profile height, rotation is from lower point
    """
    def __init__(self, pos, size=0.5, width=1, vertical_shift=0., rotation=0.):
        self.pos = pos
        if isinstance(size, (list, tuple, np.ndarray, euklid.vector.Vector2D)):
            width = size[0]/size[1]
            self.size = size[1]
        else:
            self.size = size
        self.vertical_shift = vertical_shift
        self.rotation = rotation  # rotation around lower point
        self.width = width

    def get_3d(self, rib, num=20):
        hole = self.get_curves(rib, num=num)
        return [rib.align_all(c) for c in hole]

    def get_flattened(self, rib, num=80, scale=True):
        points = self.get_curves(rib, num)
        if scale:
            points = [l.scale(rib.chord) for l in points]
        
        return points

    def get_curves(self, rib, num=80) -> List[euklid.vector.PolyLine2D]:
        lower = rib.profile_2d.get(self.pos)
        upper = rib.profile_2d.get(-self.pos)

        diff = upper - lower
        if self.rotation:
            diff = euklid.vector.Rotation2D(self.rotation).apply(diff)
        
        center = lower + diff * (0.5 + self.vertical_shift/2)
        outer_point = center + diff*self.size/2

        circle = Ellipse.from_center_p2(center, outer_point, self.width)

        return [circle.get_sequence(num)]
    
    def get_centers(self, rib, scale=False) -> List[euklid.vector.Vector2D]:
        # TODO: remove and use a polygon.centerpoint
        lower = rib.profile_2d.get(self.pos)
        upper = rib.profile_2d.get(-self.pos)

        diff = upper - lower
        if self.rotation:
            diff = euklid.vector.Rotation2D(self.rotation).apply(diff)
        
        return [lower + diff * (0.5 + self.vertical_shift/2)]



    def __json__(self):
        return {
            "pos": self.pos,
            "size": self.size,
            "vertical_shift": self.vertical_shift,
            "rotation": self.rotation}


class RibSquareHole(RibHole):
    def __init__(self, x, width, height, corner_size=0.9):
        self.x = x
        self.width = width
        self.height = height
        self.corner_size = corner_size

    def get_centers(self, rib, scale=False) -> List[euklid.vector.Vector2D]:
        return [rib.profile_2d.align([self.x, 0])]

    def get_curves(self, rib, num=80) -> List[euklid.vector.PolyLine2D]:
        x1 = self.x - self.width/2
        x2 = self.x + self.width/2

        # y -> [-1, 1]
        corner_height = (1-self.corner_size) * self.height
        corner_width = (1-self.corner_size) * self.width/2        

        controlpoints = [
            [x1, 0],
            [x1, corner_height],
            [x1, self.height],
            [self.x - corner_width, self.height],
            [self.x, self.height],
            [self.x + corner_width, self.height],
            [x2, self.height],
            [x2, corner_height],
            [x2, 0],
            [x2, -corner_height],
            [x2, -self.height],
            [self.x + corner_width, -self.height],
            [self.x, -self.height],
            [self.x - corner_width, -self.height],
            [x1, -self.height],
            [x1, -corner_height],
            [x1, 0]
        ]

        curve = euklid.spline.BSplineCurve([rib.profile_2d.align(p) for p in controlpoints])

        return [curve.get_sequence(num)]

    def __json__(self):
        return {
            }

class MultiSquareHole(RibHole):
    def __init__(self, start, end, height, num_holes, border_width):
        self.start = start
        self.end = end
        self.height = height
        self.num_holes = num_holes
        self.border_width = border_width

    @property
    def total_border(self) -> float:
        return (self.num_holes-1) * self.border_width

    @property
    def hole_width(self):

        width = (self.end - self.start - self.total_border) / self.num_holes
        if width < 1e-5:
            raise ValueError(f"Cannot fit {self.num_holes} with border: {self.border_width}")

        return width
    
    @property
    def hole_x_values(self):
        hole_width = self.hole_width

        x = self.start + hole_width/2

        return [x + i*(hole_width+self.border_width) for i in range(self.num_holes)]
    
    def get_centers(self, rib, scale=False) -> List[euklid.vector.Vector2D]:
        return [rib.profile_2d.align([x, 0]) for x in self.hole_x_values]
    
    def get_curves(self, rib, num=80) -> List[euklid.vector.PolyLine2D]:
        hole_width = self.hole_width

        curves = []
        for center in self.hole_x_values:
            hole = RibSquareHole(center, hole_width, self.height)

            curves += hole.get_curves(rib, num)
        
        return curves



class Mylar(object):
    pass

