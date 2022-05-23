import copy
import math

import numpy as np
import euklid

import openglider


class ArcSinc:
    def __init__(self):
        self.start = 0.
        self.end = math.pi
        self.interpolate(openglider.config['asinc_interpolation_points'])

    def __call__(self, val: float) -> float:
        return self.arsinc.get_value(val)

    def interpolate(self, numpoints: int) -> None:
        data = []

        for i in range(numpoints + 1):
            phi = self.end + (i * 1. / numpoints) * (self.start - self.end)  # reverse for interpolation (increasing x_values)
            data.append([np.sinc(phi / np.pi), phi])

        self.arsinc = euklid.vector.Interpolation(data)

    @property
    def numpoints(self) -> int:
        return len(self.arsinc.nodes)

    @numpoints.setter
    def numpoints(self, numpoints):
        self.interpolate(numpoints)


class BallooningBase():
    arcsinc = ArcSinc()

    def draw(self) -> euklid.vector.PolyLine2D:
        points = []
        last_point = None

        upper = euklid.vector.Vector2D([-1, 1])
        lower = euklid.vector.Vector2D([1, -1])

        for p in self:
            if p[0] < 0:
                points.append(p * upper)
            else:
                if last_point and last_point[0] < 0:
                    amount_at_zero = self[0]
                    points.append(euklid.vector.Vector2D([0, amount_at_zero]))
                    points.append(euklid.vector.Vector2D([0, -amount_at_zero]))
                
                points.append(p * lower)
            
            last_point = p
        
        return euklid.vector.PolyLine2D(points)

    def __iter__(self):
        raise NotImplementedError(f"no iter method defined on {self.__class__}")

    def __call__(self, xval: float):
        return self.get_phi(xval)

    def __getitem__(self, xval: float):
        raise NotImplementedError()

    def get_phi(self, xval: float) -> float:
        """Get Ballooning Arc (phi) for a certain XValue"""
        return self.phi(1. / (self[xval] + 1))

    def get_tension_factor(self, xval: float) -> float:
        """Get the tension due to ballooning"""
        value =  2. * np.tan(self.get_phi(xval))
        if value == 0:
            return value
        else:
            return 1. / value

    @classmethod
    def phi(cls, baloon: float) -> float:
        """
        Return the angle of the piece of cake.
        b/l=R*phi/(R*Sin(phi)) -> Phi=arsinc(l/b)
        """
        return cls.arcsinc(baloon)
    
    def apply_splines(self) -> None:
        pass


