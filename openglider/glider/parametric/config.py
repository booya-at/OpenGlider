import re
from typing import Any, ClassVar, Self

from packaging.version import Version
import euklid
import pydantic

from openglider.lines.node import Node
from openglider.utils.dataclass import BaseModel
from openglider.utils.table import Table
from openglider.vector import unit
from openglider.vector.unit import Angle, Length
from openglider.version import __version__

adapters: dict[type, Any] = {}

def get_adapter(cls: type) -> Any:
    if cls not in adapters:
        try:
            adapter: Any = pydantic.TypeAdapter(cls).validate_python
        except pydantic.errors.PydanticSchemaGenerationError:
            adapter = cls
        
        adapters[cls] = adapter

    return adapters[cls]


class ConfigTable(BaseModel):
    @classmethod
    def _migrate_table(cls, data: dict[str, list[Any]]) -> dict[str, list[Any]]:
        return data
    
    
    @classmethod
    def read_table(cls, table: Table) -> Self:
        raw_data = {}
        for current_row in range(1, table.num_rows):
            key = str(table[current_row, 0]).lower()
            if key:
                raw_data[key] = [table[current_row, i] for i in range(1, table.num_columns)]
        
        raw_data = cls._migrate_table(raw_data)
        data = {}

        for key, value in raw_data.items():
            if key in cls.model_fields:
                target_type = cls.model_fields[key].annotation
                adapter = get_adapter(target_type)  # type: ignore

                assert target_type is not None

                if target_type == euklid.vector.Vector3D:
                    data_length = 3
                else:
                    data_length = 1
                
                try:
                    if data_length == 1:
                        data[key] = adapter(value[0])
                    else:
                        data[key] = adapter(value)
                except pydantic.ValidationError as e:
                    if value[0]is None:
                        continue
                    else:
                        raise e

        return cls(**data)
    
    table_name: ClassVar[str] = "Data"
    def get_table(self) -> Table:
        table = Table(name=self.table_name)
        table[0,0] = "Key"
        table[0,1] = "Values"

        #dct = self.model_dump()
        for i, (key, value) in enumerate(self):
            if isinstance(value, euklid.vector.Vector3D):
                value = list(value)
            elif isinstance(value, unit.Quantity):
                value = [str(value)]
            else:
                value = [value]
            
            table[i+1, 0] = key
            for column, column_value in enumerate(value):
                table[i+1,column+1] = column_value

        return table

class SewingAllowanceConfig(ConfigTable):
    table_name = "Sewing Allowance"

    general: Length = Length("10mm")
    design: Length = Length("10mm")
    trailing_edge: Length = Length("10mm")
    entry: Length = Length("10mm")
    folded: Length = Length("10mm")

class ParametricGliderConfig(ConfigTable):
    table_name = "Data"

    speed: float
    glide: float

    pilot_position: euklid.vector.Vector3D
    pilot_position_name: str = "main"

    brake_offset: euklid.vector.Vector3D = euklid.vector.Vector3D([0.05, 0, 0.4])
    brake_name: str = "brake"

    has_stabicell: bool = False
    stabi_cell_position: float = 0.7
    stabi_cell_width: float = 0.5
    stabi_cell_length: float = 0.6
    stabi_cell_thickness: float = 0.7

    use_mean_profile: bool = False
    aoa_offset: Angle | None = None
    last_profile_height: float = 0
    
    use_sag: bool = True

    version: Version = Version(__version__)

    @classmethod
    def __from_json__(cls, **data: Any) -> Self:
        for name in "pilot_position", "brake_offset":
            data[name] = euklid.vector.Vector3D(data[name])
        
        return cls(**data)

    def get_lower_attachment_points(self) -> dict[str, Node]:
        points = {
            self.pilot_position_name: self.pilot_position,
            self.brake_name: self.pilot_position + self.brake_offset
        }

        return {
            name: Node(name=name, node_type=Node.NODE_TYPE.LOWER, position=position) for name, position in points.items()
        }
    
    @classmethod
    def _migrate_table(cls, data: dict[str, list[Any]]) -> dict[str, list[Any]]:
        if (stabicell := data.pop("stabicell", None)) is not None:
            data["has_stabicell"] = stabicell


        node_data: dict[str, dict[str, float]] = {}
        node_keywords = []

        for keyword in data:
            # OLD data migration
            if match := re.match(r"ahp([xyz])(.*)", keyword):
                node_keywords.append(keyword)
                coordinate, node_name = match.groups()
                node_data.setdefault(node_name, {})
                node_data[node_name][coordinate] = float(data[keyword][0])

        if node_keywords:
            for keyword in node_keywords:
                data.pop(keyword)
            
            nodes = [
                (name, euklid.vector.Vector3D([node["x"], node["y"], node["z"]]))
                for name, node in node_data.items()
            ]
            # take the lower node as main point
            if nodes[0][1][2] > nodes[1][1][2]:
                nodes = [nodes[1], nodes[0]]
            
            data["pilot_position"] = list(nodes[0][1])
            data["pilot_position_name"] = [nodes[0][0]]
            data["brake_offset"] = list(nodes[1][1] - nodes[0][1])
            data["brake_name"] = [nodes[1][0]]
        
        return data
