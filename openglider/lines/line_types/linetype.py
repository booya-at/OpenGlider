from __future__ import annotations

from openglider.utils.dataclass import dataclass, field
from typing import Dict, List, Tuple, Union, Optional
import logging

import euklid

logging.getLogger(__name__)

registry: Dict[str, LineType] = {}

@dataclass
class LineType:
    name: str
    thickness: float
    stretch_curve: Union[List[Tuple[float, float]], float]
    min_break_load: float = None
    weight: float = 0
    sheated: bool = False
    seam_correction: float = 0
    colors: List[str] = field(default_factory=lambda: [])
    color: Optional[str] = None
    cw: float = 1.1
    
    def __post_init__(self):

        if isinstance(self.stretch_curve, float):
            stretch_curve = [
                (0, 0),
                (self.min_break_load, self.stretch_curve)
            ]
        else:
            stretch_curve = self.stretch_curve
        
        if abs(stretch_curve[0][0]-0) > 1e-3:
            stretch_curve.insert(0, [0, 0])
        
        self.stretch_interpolation = euklid.vector.Interpolation(stretch_curve, extrapolate=True)

        # TODO: REMOVE!
        self.thickness = self.thickness / 1000
        self.seam_correction = self.seam_correction / 1000

        if self.min_break_load is None:
            self.min_break_load = self.stretch_curve[-1][0]

        registry[self.name] = self
       
    def __str__(self):
        return f"linetype: {self.name}"
    
    def __repr__(self):
        return str(self)

    def get_similar_lines(self):
        lines = list(self.types.values())
        lines.remove(self)
        lines.sort(key=lambda line: abs(line.thickness - self.thickness))
        
        return lines

    def get_spring_constant(self):
        force, k = self.stretch_interpolation.nodes[-1]
        try:
            result = force / (k / 100)
        except:
            logging.warn(f"invalid stretch for line type: {self.name}")
            return 50000
            
        return result

    def get_stretch_factor(self, force):
        return 1 + self.stretch_interpolation.get_value(force) / 100

    def predict_weight(self):
        t_mm = self.thickness * 1000.
        return 0.134 * t_mm + 0.6859 * t_mm ** 2

    @classmethod
    def get(cls, name):
        #names = 
        try:
            return registry[name]
        except KeyError:
            raise KeyError("Line-type {} not found".format(name))
    
    @classmethod
    def _repr_html_(self):
        html = """
            <table>
                <thead>
                    <tr>
                        <td>name</td>
                        <td>thickness</td>
                        <td>stretch_curve</td>
                        <td>spring</td>
                        <td>resistance</td>
                        <td>weight</td>
                        <td>seam correction</td>
                        <td>Colors</td>
                    </tr>
                </thead>
                """
        
        for line_type in self.types.values():
            html += f"""
                <tr>
                    <td>{line_type.name}</td>
                    <td>{line_type.thickness*1000:.02f}</td>
                    <td>{line_type.stretch_curve}</td>
                    <td>{line_type.get_spring_constant() or 0:.0f}</td>
                    <td>{line_type.min_break_load or 0:.02f}</td>
                    <td>{line_type.weight or 0:.02f}</td>
                    <td>{line_type.seam_correction:.04f}</td>
                    <td>{line_type.colors}</td>
                </tr>

                """
        
        return html


# SI UNITS -> thickness [mm], stretch [N, %]

