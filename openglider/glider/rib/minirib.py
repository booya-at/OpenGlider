from openglider.vector.spline import Bezier


class MiniRib():
    def __init__(self, yvalue, front_cut, back_cut=1, func=None, name="minirib"):
        #Profile3D.__init__(self, [], name)

        if not func:  # Function is a bezier-function depending on front/back
            if front_cut > 0:
                points = [[front_cut, 1], [front_cut * 2. / 3 + back_cut * 1. / 3]]  #
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