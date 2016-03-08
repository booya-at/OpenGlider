from openglider.airfoil import Profile3D
from openglider.vector.spline import Bezier


class MiniRib():
    def __init__(self, yvalue, front_cut, back_cut=1, func=None, name="minirib"):
        #Profile3D.__init__(self, [], name)

        if not func:  # Function is a bezier-function depending on front/back
            if front_cut > 0:
                points = [[front_cut, 1], [front_cut * 2. / 3 + back_cut * 1. / 3, 0]]  #
            else:
                points = [[front_cut, 0]]

            if back_cut < 1:
                points = points + [[front_cut * 1. / 3 + back_cut * 2. / 3, 0], [back_cut, 1]]
            else:
                points = points + [[back_cut, 0]]

            func = Bezier(points).interpolation()

        self.__function__ = func

        self.y_value = yvalue
        self.front_cut = front_cut
        self.back_cut = back_cut

    def function(self, x):
        if self.front_cut <= abs(x) <= self.back_cut:
            return min(1, max(0, self.__function__(abs(x))))
        else:
            return 1

    def get_3d(self, cell):
        shape_with_bal = cell.basic_cell.midrib(self.y_value,
                                                       True).data
        shape_wo_bal = cell.basic_cell.midrib(self.y_value,
                                                          False).data

        points = []
        for xval, with_bal, without_bal in zip(
                cell.x_values, shape_with_bal, shape_wo_bal):
            fakt = self.function(xval)  # factor ballooned/unb. (0-1)
            point = without_bal + fakt * (with_bal - without_bal)
            points.append(point)

        return Profile3D(points)

    def get_flattened(self, cell):
        prof_3d = self.get_3d(cell)
        prof_flat = prof_3d.flatten()
        prof_normalized = prof_flat.copy().normalize()

        p1 = prof_normalized(-self.back_cut)
        p2 = prof_normalized(-self.front_cut)

        p3 = prof_normalized(self.front_cut)
        p4 = prof_normalized(self.back_cut)

