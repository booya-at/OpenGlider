import re
from typing import Self
import euklid
from openglider.lines.node import Node
from openglider.utils.dataclass import BaseModel
from openglider.utils.table import Table
from openglider.version import __version__

class ParametricGliderConfig(BaseModel):
    speed: float
    glide: float

    pilot_position: euklid.vector.Vector3D
    pilot_position_name: str = "main"

    brake_offset: euklid.vector.Vector3D = euklid.vector.Vector3D([0.05, 0, 0.4])
    brake_name: str = "brake"

    has_stabicell: bool = False
    version: str = __version__

    def get_lower_attachment_points(self) -> dict[str, Node]:
        points = {
            self.pilot_position_name: self.pilot_position,
            self.brake_name: self.pilot_position + self.brake_offset
        }

        return {
            name: Node(node_type=Node.NODE_TYPE.LOWER, position=position) for name, position in points.items()
        }

    @classmethod
    def read_table(cls, table: Table) -> Self:
        data = {}
        node_data: dict[str, dict[str, float]] = {}

        migrations = {
            "stabicell": "has_stabicell"
        }

        current_row = 1
        while current_row < table.num_rows:
            key = str(table[current_row, 0]).lower()

            if key in migrations:
                key = migrations[key]

            if key in cls.model_fields:
                target_type = cls.model_fields[key].annotation
                assert target_type is not None

                if target_type == euklid.vector.Vector3D:
                    data_length = 3
                else:
                    data_length = 1
                
                field_data = [table[current_row, 1+i] for i in range(data_length)]
                current_row += 1

                if data_length == 1:
                    data[key] = target_type(field_data[0])
                else:
                    data[key] = target_type(field_data)
                
            
            else:
                # OLD data migration
                if match := re.match(r"ahp([xyz])(.*)", key):
                    coordinate, node_name = match.groups()
                    node_data.setdefault(node_name, {})
                    node_data[node_name][coordinate] = float(table[current_row, 1])
                else:
                    raise ValueError(f"could not match value: {key}")
                current_row += 1
        
        if len(node_data) == 2:
            nodes = [
                (name, euklid.vector.Vector3D([node["x"], node["y"], node["z"]]))
                for name, node in node_data.items()
            ]
            # take the lower node as main point
            if nodes[0][1][2] > nodes[1][1][2]:
                nodes = [nodes[1], nodes[0]]
            
            data["pilot_position"] = nodes[0][1]
            data["pilot_position_name"] = nodes[0][0]
            data["brake_offset"] = nodes[1][1] - nodes[0][1]
            data["brake_name"] = nodes[1][0]

        return cls(**data)
    
    def get_table(self) -> Table:
        table = Table()

        dct = self.model_dump()
        for i, (key, value) in enumerate(dct.items()):
            if isinstance(value, euklid.vector.Vector3D):
                value = list(value)
            else:
                value = [value]
            
            table[i, 0] = key
            for column, column_value in enumerate(value):
                table[i,column+1] = column_value

        return table
