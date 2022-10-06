from __future__ import annotations

import logging
import enum
from typing import Any, Dict, Optional

import euklid

from openglider.lines.functions import proj_force, proj_to_surface

logger = logging.getLogger(__name__)



class Node(object):
    class NODE_TYPE(enum.Enum):
        LOWER = 0
        KNOT = 1
        UPPER = 2

    def __init__(
            self,
            node_type: NODE_TYPE,
            force: Optional[euklid.vector.Vector3D] = None,
            position_vector: Optional[euklid.vector.Vector3D] = None,
            name: str = "unnamed_node"
            ):

        self.type = node_type  # lower, middle, top (0, 1, 2)
        self._vec = position_vector or euklid.vector.Vector3D()
        self.vec_proj = self._vec
        self.force = force or euklid.vector.Vector3D() # top-node force
        self.name = name
    
    def __json__(self) -> Dict[str, Any]:
        return{
            'node_type': self.type.name,
            'position_vector': list(self.vec),
            "name": self.name
        }
    
    @classmethod
    def __from_json__(cls, **kwargs: Any) -> Node:
        node_type_name: str = kwargs.pop("node_type")
        node_type: Node.NODE_TYPE = getattr(cls.NODE_TYPE, node_type_name)

        _force = kwargs.pop("force", None)

        if _force and isinstance(_force, (list, euklid.vector.Vector3D)):
            force = euklid.vector.Vector3D(_force)
        else:
            force = euklid.vector.Vector3D()

        node = cls(
            node_type=node_type,
            force=force
        )

        if "name" in kwargs:
            node.name = kwargs.pop("name")
        if "position_vector" in kwargs:
            node.vec = kwargs.pop("position_vector")
        
        return node

    @property
    def vec(self) -> euklid.vector.Vector3D:
        return self._vec

    @vec.setter
    def vec(self, value: euklid.vector.Vector3D) -> None:
        self._vec = euklid.vector.Vector3D(value)

    def calc_force_infl(self, vec: euklid.vector.Vector3D) -> euklid.vector.Vector3D:
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

    def calc_proj_vec(self, v_inf: euklid.vector.Vector3D) -> None:
        self.vec_proj = self.vec - v_inf * (v_inf.dot(self.vec) / v_inf.dot(v_inf))

    def get_diff(self) -> euklid.vector.Vector3D:
        return self.vec - self.vec_proj

    def is_upper(self) -> bool:
        return self.type == self.NODE_TYPE.UPPER

    def copy(self) -> Node:
        return self.__class__(self.type, self.force, self.vec, self.name)

    def __repr__(self) -> str:
        return super().__repr__() + f" of type: {self.type}"

