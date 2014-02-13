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
        start, point_1 = profile.profilepoint(self.pos)
        point_2 = profile.profilepoint(self.pos+self.size)[1]

        gib_arc = [[], []]  # first, second
        circle = polygon(point_1, point_2, num=num_points, is_center=True)[0]


        # Rotation-Offset so it starts outside
        second = False
        for i in range(len(circle)):
            #print(profile.contains_point(circle[i]))
            if profile.contains_point(circle[i]) or\
                    (i < len(circle) - 1 and profile.contains_point(circle[i+1])) or \
                    (i > 1 and profile.contains_point(circle[i-1])):
                gib_arc[second].append(circle[i])
                #print("Ok")
                #pass
            else:
                #print("no")
                second = True
        # Cut first and last
        gib_arc = gib_arc[1] + gib_arc[0]  # [secondlist] + [firstlist]
        gib_arc[0], start = profile.cut(gib_arc[0], gib_arc[1], start)
        gib_arc[-1], stop = profile.cut(gib_arc[-2], gib_arc[-1], start)
        # Append Profile_List
        gib_arc += profile.get(start, stop).tolist()

        # insert into ribs
        #return circle
        return gib_arc


class RibHole(object):
    def __init__(self, rib_no, pos, size=0.5, numpoints=20):
        self.rib_no = rib_no
        self.pos = pos
        self.size = size
        self.numpoints = numpoints

    def get_3d(self, glider, num=20):
        rib = glider.ribs[self.rib_no]
        hole = self.get_flattened(glider, num=num)
        return [rib.align([p[0], p[1], 0]) for p in hole]

    def get_flattened(self, glider, num=20):
        rib = glider.ribs[self.rib_no]
        p1 = rib.profile_2d.profilepoint(self.pos)[1]
        p2 = rib.profile_2d.profilepoint(-self.pos)[1]
        return polygon(p1, p2, num=num, size=self.size, is_center=False)[0]



class Mylar(object):
    pass

