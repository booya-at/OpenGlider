import importlib
import logging
from typing import Dict

from openglider.materials.material import Material

logger = logging.getLogger(__name__)

class MaterialRegistry:
    base_type = Material
    def __init__(self, *paths: str):
        self.materials: Dict[str, Material] = {}
        for path in paths:
            self.register(path)

    def __repr__(self) -> str:
        out = "Materials: "
        for material_name in self.materials:
            out += f"\n    - {material_name}"

        return out

    def register(self, path: str) -> None:
        module = importlib.import_module(path)

        if not hasattr(module, "materials"):
            raise Exception(f"can't register module: {path} ('materials' not defined)")

        for material in module.materials:
            self.materials[str(material).lower()] = material
    
    def get(self, name: str) -> Material:
        name = name.lower()
        if name in self.materials:
            return self.materials[name]

        #logger.warning(f"material not found: {name}")

        return self.base_type(name=name)


cloth = MaterialRegistry(
    "openglider.materials._cloth.porcher",
    "openglider.materials._cloth.other"
)