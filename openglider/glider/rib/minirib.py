from openglider.airfoil import Profile3D
from openglider.vector.spline import Bezier


class MiniRib:
    def __init__(self, yvalue, front_cut, back_cut=1, func=None, name="minirib", te_factor=None):
        """
        func(x): share of the ballooning kept at the minirib (0..1, x = chord fraction); the cell is split into
        two child cells there, each ballooned so that the panel keeps its length (bulges left and right of it).
        te_factor: a trailing edge minirib (back_cut 1): the ballooning goes by a monotone spline from 1 at the
        front_cut (flat there) to te_factor at the first third of the minirib and to 0 at the trailing edge
        (e.g. 0.25: the centre of the cell held at 1/4 of the original bulge, the trailing edge sharp).
        Without it: the Bezier 1 -> 0 within the first third.
        """
        # Profile3D.__init__(self, [], name)
        self.te_factor = te_factor
        if not func and te_factor is not None and back_cut >= 1 and front_cut > 0:
            from scipy.interpolate import PchipInterpolator

            length = 1.0 - front_cut
            spline = PchipInterpolator(
                [front_cut - 0.1 * length, front_cut, front_cut + length / 3, 1.0],
                [1.0, 1.0, te_factor, 0.0],
            )
            func = lambda x: float(spline(x))  # noqa: E731

        if not func:  # Function is a bezier-function depending on front/back
            if front_cut > 0:
                points = [
                    [front_cut, 1],
                    [front_cut * 2.0 / 3 + back_cut * 1.0 / 3, 0],
                ]  #
            else:
                points = [[front_cut, 0]]

            if back_cut < 1:
                points = points + [
                    [front_cut * 1.0 / 3 + back_cut * 2.0 / 3, 0],
                    [back_cut, 1],
                ]
            else:
                points = points + [[back_cut, 0]]

            func = Bezier(points).interpolation()

        self.__function__ = func

        self.y_value = yvalue
        self.front_cut = front_cut
        self.back_cut = back_cut

    def __json__(self):
        # func is not stored (rebuilt from front / back cut and te_factor)
        return {"yvalue": self.y_value, "front_cut": self.front_cut, "back_cut": self.back_cut,
                "name": getattr(self, "name", "minirib"), "te_factor": self.te_factor}

    def function(self, x):
        if self.front_cut <= abs(x) <= self.back_cut:
            return min(1, max(0, self.__function__(abs(x))))
        else:
            return 1

    def get_3d(self, cell):
        shape_with_bal = cell.basic_cell.midrib(self.y_value, True).data
        shape_wo_bal = cell.basic_cell.midrib(self.y_value, False).data

        points = []
        for xval, with_bal, without_bal in zip(
            cell.x_values, shape_with_bal, shape_wo_bal
        ):
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
