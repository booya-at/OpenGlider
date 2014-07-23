from pivy import coin
from openglider.utils.bezier import BezierCurve
import numpy
from openglider.vector import normalize

class Line(object):
    def __init__(self, points):
        self.object = coin.SoSeparator()
        self.ls = coin.SoLineSet()
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.points = points
        self.update()
        self.object.addChild(self.color)
        self.object.addChild(self.data)
        self.object.addChild(self.ls)

    def update(self, points=None):
        if points is not None:
            self.points = points
        self.color.diffuseColor.setValue(0, 0, 0)
        self.data.point.setValue(0, 0, 0)
        self.data.point.setValues(0, len(self.points), self.points)


class Spline(Line):
    def __init__(self, control_points, num=50):
        self.bezier_curve = BezierCurve(controlpoints=control_points)
        self.num_points = num
        super(Spline, self).__init__(self.bezier_curve.get_sequence(num))

    def update(self, points=None):
        if points is not None:
            self.bezier_curve.controlpoints = points
        super(Spline, self).update(points=[self.bezier_curve(i * 1. / (self.num - 1)) for i in range(self.num)])

    @property
    def num(self):
        return self.num_points

    @num.setter
    def num(self, num):
        self.numpoints = num
        self.update(self.bezier_curve.controlpoints)


def mirror_func(direction=[0, 1, 0]):
    x, y, z = normalize(direction)
    mirrormat = numpy.array(
        [
            [1 - 2 * x ** 2, -2 * x * y, -2 * x * z],
            [-2 * x * y, 1 - 2 * y ** 2, -2 * y * z],
            [-2 * x * z, -2 * y * z, 1 - 2 * z ** 2]
        ]
    )
    def reflect(vec):
        if isinstance(vec[0], (numpy.ndarray, list, tuple)):
            return numpy.array([reflect(i) for i in vec]).tolist()
        else:
            return numpy.dot(vec, mirrormat).tolist()

    return reflect

reflect_x = mirror_func(direction=[1, 0, 0])
reflect_y = mirror_func(direction=[0, 1, 0])
reflect_z = mirror_func(direction=[0, 0, 1])


if __name__ == "__main__":
    a = [[1,2,3], [2,3,4]]
    print(reflect_y(a))

