class Material:
    weight: float = 0 # g / sqm
    
    manufacturer: str = "unknown"
    name: str = "unnamed"
    color: str = ""
    color_code: int = int("FFFFFF", base=16)

    def __init__(self, **kwargs):
        if "color_code" in kwargs:
            color_code = kwargs.pop("color_code")
            color_code_int = int(color_code, base=16)

            if color_code_int < 0 or color_code_int > int("FFFFFF", base=16):
                raise ValueError(f"invalid color code: {color_code}")
        
            self.color_code = color_code
        
        for arg, value in kwargs.items():
            if not hasattr(self, arg):
                raise ValueError(f"invalid attribute: {arg}")
        
            setattr(self, arg, value)

    def __str__(self):
        full_name = f"{self.manufacturer}.{self.name}"
        
        if self.color:
            full_name += f".{self.color}"
        
        return full_name
    
    def __repr__(self):
        return f"<Material: {self.__str__()}>"

    def __json__(self):
        return {
            "name": str(self)
        }
    
    @classmethod
    def __from_json__(cls, name):
        import openglider.materials
        return openglider.materials.cloth.get(name)