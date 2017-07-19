import random
import unittest

from visual_test_glider import GliderTestClass
import common

import openglider
from openglider.glider.rib import RibHole, RigidFoil, GibusArcs #, Mylar
import openglider.graphics as Graph
from openglider.vector import norm, PolyLine2D


class TestRibElements(GliderTestClass):
    def setUp(self):
        super(TestRibElements, self).setUp()
        attachent_points = []
        rib = None

        while not attachent_points:
            rib_no = random.randint(0, len(self.glider.ribs)-2)
            rib = self.glider.ribs[rib_no]
            att = [n for n in self.glider.lineset.nodes if n.type == 2]
            attachent_points = [n for n in att if n.rib is rib]

        print(rib_no)
        self.attachment_points = attachent_points
        self.rib = rib

    @unittest.skip("whatsoever!")
    def get_gibus_arcs(self, x):
        gibus_arc = GibusArcs(position=x, size=0.02)
        thalist = gibus_arc.get_3d(self.rib, num_points=10)

        return Graph.Polygon(thalist)

    def get_hole(self, x, size=0.4):
        hole = RibHole(x, size=size)
        return Graph.Polygon(hole.get_3d(self.rib))

    def get_rigid(self, start, stop):
        rigid = RigidFoil(start, stop)
        #return Graph.Line([self.rib.align(p, scale=False) for p in rigid.get_flattened(self.rib)])
        return Graph.Line(rigid.get_3d(self.rib))

    def get_all(self):
        gib_pos = [n.rib_pos for n in self.attachment_points]
        gib_pos.sort()
        hole_pos = [(x1+x2)/2 for x1,x2 in zip(gib_pos[:-1], gib_pos[1:])]

        gibs = [self.get_gibus_arcs(y) for y in gib_pos]
        holes = [self.get_hole(x, 0.4) for x in hole_pos]
        rigid = self.get_rigid(-.15, .13)

        p = self.rib.profile_2d
        print(max([norm(p[0]- p2) for p2 in p]), self.rib.chord)

        return [Graph.Line(self.rib.profile_3d.data)] + gibs + holes + [rigid]

    @unittest.skip("whatsoever!")
    def test_all_2(self):
        a = self.get_all()
        self.setUp()
        b = self.get_all()

        Graph.Graphics(a + b)

    def test_flat(self):
        prof = self.rib.profile_2d.copy()
        prof = PolyLine2D(prof.data) * [self.rib.chord, self.rib.chord]


        print(self.rib.profile_2d, prof)
        #prof.scale(self.rib.chord)
        gib_pos = [n.rib_pos for n in self.attachment_points]
        gib_pos.sort()
        hole_pos = [(x1+x2)/2 for x1,x2 in zip(gib_pos[:-1], gib_pos[1:])]


        rigid = RigidFoil(-.15, .12)
        r_flat = rigid.get_flattened(self.rib)

        print(self.rib.rotation_matrix, norm(self.rib.rotation_matrix.dot([2,0,0])))
        Graph.Graphics([Graph.Line(prof), Graph.Line(self.rib.profile_2d.data * self.rib.chord), Graph.Line(r_flat)])

        Graph.Graphics([Graph.Line([self.rib.align(p, scale=False) for p in prof.data]),
                        Graph.Line([self.rib.align(p, scale=False) for p in r_flat]),
                        Graph.Line(self.rib.profile_3d.data)
                        ])



    # def test_hole(self):
    #     rib_no = random.randint(0, len(self.glider.ribs)-1)
    #     thalist = hole.get_3d()
    #     Graph.Graphics([Graph.Line(self.glider.ribs[rib_no].profile_3d.data),
    #                     Graph.Polygon(thalist)])


if __name__ == '__main__':
    unittest.main()