from __future__ import annotations

from typing import Any, Dict
from openglider.materials import Material
from openglider.utils.dataclass import BaseModel, Field
from openglider.utils.table import Table

class MaterialUsage(BaseModel):
    usage: Dict[Material | None, float] = Field(default_factory=dict)
    
    
    def __repr__(self) -> str:
        result = "<MaterialUsage "
        for material, amount in self.usage.items():
            result += f"\n\t- {material}: {amount:.3f}"
        
        result += "\n\t>"

        return result
    
    def consume(self, material: Material | None, amount: float) -> MaterialUsage:
        self.usage.setdefault(material, 0)
        self.usage[material] += amount
    
        return self

    def copy(self, **kwargs: Any) -> MaterialUsage:
        new = MaterialUsage()
        for material, value in self.usage.items():
            new.consume(material, value)
        
        return new
    
    def __mul__(self, value: float) -> MaterialUsage:
        new = MaterialUsage()
        for material, usage in self.usage.items():
            new.consume(material, usage*value)
        
        return new
    
    def __add__(self, other: MaterialUsage) -> MaterialUsage:
        new = self.copy()

        for material, amount in other.usage.items():
            new.consume(material, amount)
        
        return new
    
    def total(self) -> float:
        return sum(self.usage.values())

    
    def weight(self) -> float:
        weight = 0.
        for material, usage in self.usage.items():
            if material is not None:
                weight += material.weight * usage
        
        return weight
    
    def get_table(self, header: str=None) -> Table:
        table = Table()
        i = 0

        if header is not None:
            table[0,0] = header
            i = 1

        for material, usage in self.usage.items():
            table[i, 0] = str(material)
            table[i, 1] = round(usage, 3)
            if material is not None:
                table[i, 2] = round(usage*material.weight, 1)
            
            i += 1
        
        return table
