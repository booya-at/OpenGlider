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


