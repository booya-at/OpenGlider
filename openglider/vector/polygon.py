from openglider.vector import PolyLine2D
from openglider.vector.functions import cut


class Polygon2D(PolyLine2D):
    @property
    def isclosed(self):
        return self.data[0] == self.data[-1]

    def close(self):
        """
        Close the endings of the polygon using a cut.
        Return: success
        """
        try:
            thacut = cut(self.data[0], self.data[1], self.data[-2], self.data[-1])
            if thacut[1] <= 1 and 0 <= thacut[2]:
                self.data[0] = thacut[0]
                self.data[-1] = thacut[0]
                return True
        except ArithmeticError:
            return False

    #@cached-property(self)
    @property
    def centerpoint(self):
        # todo: http://en.wikipedia.org/wiki/Polygon#Area_and_centroid
        """
        Return the average point of the polygon.
        """
        return sum(self.data) / len(self.data)

    @property
    def area(self):
        # http://en.wikipedia.org/wiki/Polygon#Area_and_centroid
        area = 0
        n = len(self)-1
        for i in range(len(self)):
            i2 = (i+1) % n
            area += self[i][0]*self[i2][1] - self[i][1]*self[i2][0]

        return area/2

    def contains_point(self, point):
        """
        Check if a Polygon contains a point or not.
        reference: http://en.wikipedia.org/wiki/Point_in_polygon

        :returns: boolean
        """
        # using ray-casting-algorithm
        cuts = self.cut(point, self.centerpoint, cut_only_positive=True)
        return bool(sum(1 for _ in cuts) % 2)
        # todo: alternative: winding number