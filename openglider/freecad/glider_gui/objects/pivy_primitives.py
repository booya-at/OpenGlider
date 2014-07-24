from pivy import coin
from openglider.utils.bezier import BezierCurve
import numpy

class Line(object):
    def __init__(self, points):
        self.object = coin.SoSeparator()
        self.ls = coin.SoLineSet()
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.points = vector3D(points)
        self.update()
        self.object.addChild(self.color)
        self.object.addChild(self.data)
        self.object.addChild(self.ls)

    def update(self, points=None):
        if points is not None:
            self.points = vector3D(points)
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
            self.bezier_curve.controlpoints = vector3D(points)
        super(Spline, self).update(points=[self.bezier_curve(i * 1. / (self.num - 1)) for i in range(self.num)])

    @property
    def num(self):
        return self.num_points

    @num.setter
    def num(self, num):
        self.numpoints = num
        self.update(self.bezier_curve.controlpoints)

def vector3D(vec):
    if not isinstance(vec[0], (list, tuple, numpy.ndarray)):
        if len(vec) == 3:
            return vec
        elif len(vec) == 2:
            return numpy.array(vec).tolist() + [0.]
        else:
            print("something wrong with this list: ", vec)
    else:
        return [vector3D(i) for i in vec]


if __name__ == "__main__":
    print(vector3D([[0, 1], [2, 3]]))



