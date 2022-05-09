from __future__ import annotations

import logging
import enum

import euklid

from openglider.lines.functions import proj_force, proj_to_surface

logger = logging.getLogger(__name__)



class Node(object):
    class NODE_TYPE(enum.Enum):
        LOWER = 0
        KNOT = 1
        UPPER = 2

    def __init__(self, node_type: NODE_TYPE, force=None, position_vector=None, attachment_point=None, name=None):
        self.type = node_type  # lower, middle, top (0, 1, 2)
        if position_vector is None:
            position_vector = [0,0,0]
        self._vec = euklid.vector.Vector3D(position_vector)

        self.vec_proj = self._vec
        self.force = force or euklid.vector.Vector3D() # top-node force
        self.attachment_point = attachment_point
        self.name = name or "name_not_set"
    
    def __json__(self):
        return{
            'node_type': self.type.name,
            'position_vector': list(self.vec),
            "name": self.name
        }
    
    @classmethod
    def __from_json__(cls, **kwargs) -> Node:
        if "node_type" in kwargs:
            node_type = getattr(cls.NODE_TYPE, kwargs.pop("node_type"))
        else:
            node_type = None
        force = kwargs.pop("force", None)

        if force and isinstance(force, list):
            force = euklid.vector.Vector3D(force)

        return cls(
            node_type=node_type,
            force=force,
            **kwargs
        )

    @property
    def vec(self) -> euklid.vector.Vector3D:
        return self._vec

    @vec.setter
    def vec(self, value):
        self._vec = euklid.vector.Vector3D(value)

    def calc_force_infl(self, vec) -> euklid.vector.Vector3D:
        v = euklid.vector.Vector3D(vec)

        direction = self.vec - v
        if self.type == self.NODE_TYPE.UPPER:
            force = proj_force(self.force, direction)
        else:
            force = direction.normalized().dot(self.force)
        if force is None:
            logging.warn("projected force for line {} is None, direction: {}, force: {}".format(
                self.name, direction, self.force))
            force = 0.00001

        return direction.normalized() * force

    def get_position(self):
        pass

    def calc_proj_vec(self, v_inf) -> None:
        self.vec_proj = self.vec - v_inf * (v_inf.dot(self.vec) / v_inf.dot(v_inf))

    def get_diff(self) -> euklid.vector.Vector3D:
        return self.vec - self.vec_proj

    def is_upper(self) -> bool:
        return self.type == self.NODE_TYPE.UPPER

    def copy(self) -> Node:
        return self.__class__(self.type, self.vec, self.attachment_point, self.name)

    def __repr__(self) -> str:
        return super().__repr__() + f" of type: {self.type}"

