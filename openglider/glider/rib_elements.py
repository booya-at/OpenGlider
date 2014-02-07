

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

    def get_3d(self, glider):
        pass

    def get_flattened(self, glider, ribs_2d):
        pass


class RibHole(object):
    def __init__(self):
        pass

    def get_3d(self):
        pass

    def get_flattened(self):
        pass


class Mylar(object):
    pass

