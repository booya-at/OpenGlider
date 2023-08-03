from typing import List, Union, Optional, overload

import euklid
import pyfoil

from openglider.utils.cache import cached_property

class Profile3D:
    def __init__(self, data: euklid.vector.PolyLine3D, name: str="unnamed") -> None:
        self.curve = euklid.vector.PolyLine3D(data)
        self.name = name

    @overload
    def __getitem__(self, ik: float) -> euklid.vector.Vector3D: ...

    @overload
    def __getitem__(self, ik: slice) -> euklid.vector.PolyLine3D: ...

    def __getitem__(self, ik: float | slice) -> euklid.vector.PolyLine3D | euklid.vector.Vector3D:
        if isinstance(ik, slice):
            start = ik.start
            stop = ik.stop
            if ik.step == -1:
                stop, start = start, stop
            elif ik.step not in (None, 1):
                raise Exception(f"invalid step: {ik.step}")
            
            return self.curve.get(start, stop)

        return self.curve.get(ik)
    
    def __len__(self) -> int:
        return len(self.curve)
    
    def get_positions(self, start: float, stop: float) -> list[float]:
        return self.curve.get_positions(start, stop)

    @overload
    def get(self, start: float) -> euklid.vector.Vector3D: ...

    @overload
    def get(self, start: float, stop: float) -> euklid.vector.PolyLine3D: ...


    def get(self, start: float, stop: float | None=None) -> euklid.vector.PolyLine3D | euklid.vector.Vector3D:
        if stop is None:
            return self.curve.get(start)
            
        return self.curve.get(start, stop)

    @cached_property('self')
    def noseindex(self) -> int:
        p0 = self.curve.nodes[0]
        max_dist = 0.
        noseindex = 0
        for i, p1 in enumerate(self.curve.nodes):
            diff = (p1 - p0).length()
            if diff > max_dist:
                noseindex = i
                max_dist = diff
        return noseindex

    @cached_property('self')
    def projection_layer(self) -> euklid.plane.Plane:
        """
        Projection Layer of profile_3d
        """
        p1 = self.curve.nodes[0]
        diff = [p - p1 for p in self.curve.nodes]



        xvect = diff[self.noseindex].normalized() * -1
        yvect = euklid.vector.Vector3D([0, 0, 0])

        for i in range(len(diff)):
            sign = 1 - 2 * (i > self.noseindex)
            yvect = yvect + (diff[i] - xvect * xvect.dot(diff[i])) * sign

        yvect = yvect.normalized()

        return euklid.plane.Plane(self.curve.nodes[self.noseindex], xvect, yvect)

    def flatten(self) -> pyfoil.Airfoil:
        """Flatten the airfoil and return a 2d-Representative"""
        layer: euklid.plane.Plane = self.projection_layer
        return pyfoil.Airfoil([layer.project(p) for p in self.curve.nodes],
                         name=self.name or 'profile' + "_flattened")

    @cached_property('self')
    def normvectors(self) -> list[euklid.vector.Vector3D]:
        layer = self.projection_layer
        profnorm = layer.normvector

        get_normvector = lambda x: x.cross(profnorm).normalized()

        vectors = [get_normvector(self.curve.nodes[1] - self.curve.nodes[0])]
        for i in range(1, len(self.curve.nodes) - 1):
            vectors.append(get_normvector(
                (self.curve.nodes[i + 1] - self.curve.nodes[i]).normalized() +
                (self.curve.nodes[i] - self.curve.nodes[i - 1]).normalized()
                ))
        vectors.append(get_normvector(self.curve.nodes[-1] - self.curve.nodes[-2]))

        return vectors

    @property
    def tangents(self) -> list[euklid.vector.Vector3D]:
        return self.curve.get_tangents()