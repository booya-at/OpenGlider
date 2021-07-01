import importlib
import logging

from openglider.materials.material import Material

logger = logging.getLogger(__name__)

class MaterialRegistry:
    base_type = Material
    def __init__(self, *paths):
        self.materials = {}
        for path in paths:
            self.register(path)

    def __repr__(self):
        out = "Materials: "
        for material_name in self.materials:
            out += f"\n    - {material_name}"

        return out

    def register(self, path):
        module = importlib.import_module(path)

        for material in module.materials:
            self.materials[str(material).lower()] = material
    
    def get(self, name: str):
        name = name.lower()
        if name in self.materials:
            return self.materials[name]

        logger.warning(f"material not found: {name}")

        return self.base_type(name=name)


cloth = MaterialRegistry(
    "openglider.materials._cloth.porcher"
)