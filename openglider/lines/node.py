from __future__ import annotations

import logging
import enum
from typing import Any

import euklid

from openglider.lines.functions import proj_force
from openglider.utils.dataclass import BaseModel, Field

logger = logging.getLogger(__name__)

class NODE_TYPE_ENUM(enum.Enum):
    LOWER = 0
    KNOT = 1
    UPPER = 2


class Node(BaseModel):
    NODE_TYPE = NODE_TYPE_ENUM

    node_type: NODE_TYPE_ENUM
    force: euklid.vector.Vector3D = Field(default_factory=lambda: euklid.vector.Vector3D())
    position: euklid.vector.Vector3D = Field(default_factory=lambda: euklid.vector.Vector3D())
    vec_proj: euklid.vector.Vector3D = Field(default_factory=lambda: euklid.vector.Vector3D())
    name: str = "unnamed_node"
    
    def __json__(self) -> dict[str, Any]:
        return{
            'node_type': self.node_type.name,
            'position': list(self.position),
            "name": self.name
        }
    
    @classmethod
    def __from_json__(cls, **kwargs: Any) -> Node:
        node_type_name: str = kwargs.pop("node_type")
        node_type: NODE_TYPE_ENUM = getattr(cls.NODE_TYPE, node_type_name)

        return cls(
            node_type=node_type,
            **kwargs
        )

    def calc_force_infl(self, vec: euklid.vector.Vector3D) -> euklid.vector.Vector3D:
        v = euklid.vector.Vector3D(vec)

        direction = self.position - v
        if self.node_type == self.NODE_TYPE.UPPER:
            force = proj_force(self.force, direction)
        else:
            force = direction.normalized().dot(self.force)
        if force is None:
            logging.warn("projected force for line {} is None, direction: {}, force: {}".format(
                self.name, direction, self.force))
            force = 0.00001

        return direction.normalized() * force

    def calc_proj_vec(self, v_inf: euklid.vector.Vector3D) -> None:
        self.vec_proj = self.position - v_inf * (v_inf.dot(self.position) / v_inf.dot(v_inf))

    def get_diff(self) -> euklid.vector.Vector3D:
        return self.position - self.vec_proj

    def is_upper(self) -> bool:
        return self.node_type == self.NODE_TYPE.UPPER

    def __repr__(self) -> str:
        return super().__repr__() + f" of type: {self.node_type}"

