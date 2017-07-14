import numpy

from openglider.vector.functions import normalize


class Plane(object):
    def __init__(self, p0, v1, v2):
        self.p0 = numpy.array(p0)
        self.v1 = numpy.array(v1)
        self.v2 = numpy.array(v2)

    def point(self, x1, x2):
        return self.p0 + x1 * self.v1 + x2 * self.v2

    def cut(self, p1, p2):
        """
        cut two points
        eq: p1 + x1*(p2-p1) = self.p0 + x2 * self.v1 + x3*self.r2
        - x1*(p2-p1) + x2 * self.v1 + x3 * self.v2 = p1 - self.p0
        """
        lhs = numpy.matrix([p1-p2, self.v1, self.v2]).transpose()
        rhs = p1 - self.p0
        res = numpy.linalg.solve(lhs, rhs)
        print("res: ", res, lhs, rhs)
        return res[0], res[1:], self.point(res[1], res[2])

    def projection(self, point):
        diff = point - self.p0
        return [self.v1.dot(diff), self.v2.dot(diff)]

    @property
    def translation_matrix(self):
        return numpy.matrix([self.v1, self.v2, self.normvector]).transpose()

    def align(self, point_3d):
        return self.p0 + self.translation_matrix.dot(point_3d)

    def normalize(self):
        self.v1 = normalize(self.v1)
        self.v2 = normalize(self.v2 - self.v1 * self.v1.dot(self.v2))

    @property
    def normvector(self):
        return numpy.cross(self.v1, self.v2)

    @normvector.setter
    def normvector(self, normvector):
        #assert isinstance(normvector, np.ndarray)
        # todo: fix // write test
        self.v1 = numpy.array([1,1,1])
        self.v1 = self.v1 - self.v1 * normvector
        #self.v1 = numpy.array([0, -normvector[3], normvector[2]])
        self.v2 = numpy.cross(self.v1, normvector)

    @classmethod
    def from_point_cloud(cls, points):
        # TODO: p0
        mat = numpy.array(points).T
        mat = numpy.array([mat[0], mat[1], mat[2], np.ones(len(mat[0]))])
        u, d, v = numpy.linalg.svd(mat.T)
        n = v[-1][0:3]
        l_n = numpy.linalg.norm(n)
        n /= l_n
        x = numpy.cross(n, n[::-1])
        y = numpy.cross(n, x)
        #return cls(p0, x,y)

