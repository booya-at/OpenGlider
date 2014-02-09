from openglider import Profile2D
from openglider.Utils.marks import polygon
from openglider.Vector import cut


class RigidFoil(object):
    def __init__(self):
        pass

    def get_3d(self, glider):
        ######NEEDED??
        pass

    def get_flattened(self, glider, ribs_2d):
        pass


class GibusArcs(object):
    def __init__(self, rib_no, position, size=0.2):
        """A Reinforcement in the form of an arc, in the shape of an arc, to reinforce attachment points"""
        self.rib_no = rib_no
        self.pos = position
        self.size = size

    def get_3d(self, glider, num_points=10):
        # create circle with center on the point
        gib_arc = self.get_flattened(glider, num_points=num_points)
        rib = glider.ribs[self.rib_no]
        return [rib.align([p[0], p[1], 0]) for p in gib_arc]

    def get_flattened(self, glider, ribs_2d=None, num_points=10):
        # get center point
        profile = glider.ribs[self.rib_no].profile_2d
        point_1 = profile.profilepoint(self.pos)[1]
        point_2 = profile.profilepoint(self.pos+self.size)[1]

        gib_arc = []
        #profile = Profile2D()
        circle = polygon(point_1, point_2, num=num_points, is_center=True, rotation=0.1)[0]
        #print(len(circle))
        for i in range(len(circle)):
            #print(profile.contains_point(circle[i]))
            if profile.contains_point(circle[i]):
                gib_arc.append(circle[i])
                print("Ok")
            elif profile.contains_point(circle[i-1]):
                #gib_arc.insert(0, circle[i])
                pass
            else:
                print("no")
        # Cut first and last
        #gib_arc[0] = profile.cut(gib_arc[0], gib_arc[1])[0]
        #gib_arc[-1] = profile.cut(gib_arc[-2], gib_arc[-1])
        # insert into ribs
        #return circle
        return gib_arc


class RibHole(object):
    def __init__(self):
        pass

    def get_3d(self):
        pass

    def get_flattened(self):
        pass


class Mylar(object):
    pass

