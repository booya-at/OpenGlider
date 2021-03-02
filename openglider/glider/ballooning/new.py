import euklid

from openglider.glider.ballooning.base import BallooningBase

class BallooningNew(BallooningBase):
    def __init__(self, interpolation: euklid.vector.Interpolation, name: str="ballooning_new"):
        self.interpolation = interpolation
        self.name = name

    def __getitem__(self, xval):
        """Get Ballooning Value (%) for a certain XValue"""
        if -1 <= xval <= 1:
            return max(0, self.interpolation.get_value(xval))
        else:
            raise ValueError("Value {} not between -1 and 1".format(xval))
    
    def __add__(self, other):
        new_interpolation = self.interpolation + other.interpolation

        return BallooningNew(new_interpolation)
    
    def __mul__(self, factor):
        return BallooningNew(self.interpolation * factor)

    def close_trailing_edge(self, start_x):
        nodes = []
        for n in self.interpolation.nodes:
            x = n[0]
            if x > start_x:
                y = n[1]
                t_e_c = start_x
                y = y * (1 - (x-t_e_c)/(1-t_e_c))
                n[1] = y
                    #y = (1-x) * y

    def copy(self):
        return BallooningNew(self.interpolation.copy(), name=self.name)


class BallooningBezierNeu(BallooningNew):
    def __init__(self, spline, name="ballooning_new"):
        self.spline_curve = euklid.vector.BSplineCurve(spline)
        self.name = name
        super(BallooningBezierNeu, self).__init__(None, None)
        self.apply_splines()

    def __json__(self):
        return {"spline": self.spline_curve.controlpoints}

    def __getitem__(self, xval):
        """Get Ballooning Value (%) for a certain XValue"""
        if -1 <= xval <= 1:
            return self.interpolation.get_value(xval)
        else:
            raise ValueError("Value {} not between -1 and 1".format(xval))

    def copy(self):
        return BallooningBezierNeu(self.spline_curve.copy().controlpoints, name=self.name)

    @classmethod
    def from_classic(cls, ballooning, numpoints=14):
        upper = ballooning.upper * [-1, 1]
        lower = ballooning.lower

        data = upper.reverse().nodes + lower.nodes

        #data = [(-p[0], p[1]) for p in upper[::-1]] + list(lower)

        spline = euklid.vector.BSplineCurve.fit(data, numpoints)
        #return data
        return cls(spline.controlpoints)

    def get_points(self, n=300):
        return self.spline_curve.get_sequence(n).nodes

    def apply_splines(self):
        self.interpolation = euklid.vector.Interpolation(self.get_points())

    def __mul__(self, factor):
        return BallooningBezierNeu(self.controlpoints.scale([1, factor]))

    def __imul__(self, factor):  # TODO: Check consistency
        """Multiplication of BezierBallooning"""
        self.scale(factor)
        self.apply_splines()
        return self

    @property
    def controlpoints(self) -> euklid.vector.PolyLine2D:
        return self.spline_curve.controlpoints

    @controlpoints.setter
    def controlpoints(self, controlpoints: euklid.vector.PolyLine2D):
        self.spline_curve.controlpoints = controlpoints
        self.apply_splines()

    def scale(self, factor):
        self.spline_curve.controlpoints = self.spline_curve.controlpoints.scale([1, factor])
        self.apply_splines()

    @property
    def amount_maximal(self):
        return max([p[1] for p in self.interpolation.nodes])

    def _repr_svg_(self):
        import svgwrite
        import svgwrite.container

        height = self.amount_maximal

        drawing = svgwrite.Drawing(size=[800, 800*height])

        drawing.viewbox(-1, -height/2, 2, height)

        g = svgwrite.container.Group()
        g.scale(1, -1)
        upper = drawing.polyline(self.spline_curve.get_sequence(100).nodes, style="stroke:black; vector-effect: non-scaling-stroke; fill: none;")
        g.add(upper)
        drawing.add(g)

        return drawing.tostring()

