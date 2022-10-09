from __future__ import annotations

from typing import TYPE_CHECKING, Any, List
import zipfile
import lxml
import json
import base64
import array
import logging

import openglider.jsonify
from openglider.glider.parametric.table import SingleSkinTable
from openglider.utils.table import Table

if TYPE_CHECKING:
    from openglider.glider.parametric.glider import ParametricGlider
    import openglider.glider.parametric


logger = logging.getLogger(__name__)


def import_freecad(path: str) -> ParametricGlider:
    fc = FreeCADFile(path)
    
    return fc.get_project()

class FreeCADFile:
    def __init__(self, path: str):
        self.path = path
        self.load()
    
    def load(self) -> None:
        self.infile = zipfile.ZipFile(self.path)
        
        xml_tree = lxml.etree.ElementTree(file=self.infile.open("Document.xml"))
        root=xml_tree.getroot()
        objects = root.find("ObjectData")
        
        self.objects = {
            o.get("name"): {
                prop.get("name"): prop for prop in o.find("Properties").findall("Property")
            } 
            
            for o in objects.getchildren()
        }
    
    def get_project(self) -> ParametricGlider:
        parametric = self._get_parametric_glider()
        for obj_name, obj in self.objects.items():
            self._process(obj_name, parametric)
            
        return parametric
        
    
    def _get_parametric_glider(self) -> ParametricGlider:
        proxy = self.objects["Glider"]["Proxy"]
        data=proxy.find("Python")
        base64_data=data.get("value")
        json_data=base64.decodebytes(base64_data.encode('utf-8'))
        parametric_glider_str = json.loads(json_data)["ParametricGlider"]
        with open("/tmp/glider.json", "w") as outfile:
            outfile.write(parametric_glider_str)
        parametric_glider = openglider.jsonify.loads(parametric_glider_str)["data"]
        
        return parametric_glider
    
    def get_property(self, object_name: str, name: str) -> Any:
        prop = self.objects[object_name][name]
        x = prop.getchildren()[0]
        
        v = x.get("value")
        
        if x.tag == "FloatList":
            return self._read_floatlist(x)
        elif x.tag == "IntegerList":
            return self._read_integerlist(x)
        elif x.tag == "Float":
            return float(v)
        elif x.tag == "Integer":
            return int(v)
        elif x.tag == "Bool":
            if v == "false":
                return False
            elif v == "true":
                return True
            else:
                raise ValueError(f"invalid value for bool: {v}")
        elif x.tag == "Python":
            return x.get("class")
        
        if value := x.get("value"):
            return value
        
        elif value := x.get("file"):
            return self._read_floatlist(value)
        
        raise Exception()
    
    def get_ribs_property(self, parametric_glider: ParametricGlider, obj_name: str, property_name: str="ribs") -> List[int]:
        ribs = self.get_property(obj_name, property_name)

        if parametric_glider.shape.has_center_cell:
            ribs_lst = [r-1 for r in ribs if r>0]
        
        return ribs_lst

        
    def _read_floatlist(self, node: Any) -> List[float]:
        filename = node.get("file")
        bytestring = self.infile.open(filename).read()
        offset=4
        float_array = array.array('d')
        float_array.frombytes(bytestring[4:])
        
        return float_array.tolist()
    
    def _read_integerlist(self, node: Any) -> List[int]:
        return [
            int(x.get("v")) for x in node.getchildren()
        ]
    
    def _process(self, obj_name: str, parametric_glider: ParametricGlider) -> None:
        obj = self.objects[obj_name]
        if "Proxy" in obj:
            classname = self.get_property(obj_name, "Proxy")
            
            if classname == "BallooningMultiplier":
                values = self.get_property(obj_name, "mutiply_values")

                table = Table()
                table[0,0] = "BallooningFactor"

                for i, factor in enumerate(values):
                    table[i+1, 0] = factor
                
                parametric_glider.tables.ballooning_factors.table.append_right(table)
            
            elif classname == "SingleSkinRibFeature":
                ribs = self.get_ribs_property(parametric_glider, obj_name)
                keyword_name = "SkinRib7"
                keyword = SingleSkinTable.keywords[keyword_name]

                attributes = [
                    self.get_property(obj_name, name) for name, _annotation in keyword.attributes
                ]

                table = Table()
                table[0,0] = keyword_name

                for rib_no in ribs:
                    for i, value in enumerate(attributes):
                        table[rib_no+1, i] = value
                
                parametric_glider.tables.rib_modifiers.table.append_right(table)

                xrot_table = Table()
                xrot_table[0,0] = "XRot"
                xrot = self.get_property(obj_name, "xrot")

                for rib_no, rot in enumerate(xrot):
                    row = rib_no
                    if not parametric_glider.shape.has_center_cell:
                        row += 1
                    elif rib_no == 0:
                        continue

                    xrot_table[row, 0] = rot

                parametric_glider.tables.rib_modifiers.table.append_right(xrot_table)
            
            elif classname == "FlapFeature":
                flap_amount = self.get_property(obj_name, "flap_amount")
                flap_begin = self.get_property(obj_name, "flap_begin")
                flap_ribs = self.get_ribs_property(parametric_glider, obj_name, "flap_ribs")

                table = Table()
                table[0,0] = "Flap"

                for rib_no in flap_ribs:
                    table[rib_no+1, 0] = flap_begin
                    table[rib_no+1, 1] = flap_amount
                
                parametric_glider.tables.profiles.table.append_right(table)
            
            elif classname == "HoleFeature":
                ribs = self.get_ribs_property(parametric_glider, obj_name)
                hole_width = self.get_property(obj_name, "hole_width")
                hole_height = self.get_property(obj_name, "hole_height")
                vertical_shift = self.get_property(obj_name, "vertical_shift")
                rotation = self.get_property(obj_name, "rotation")

                position_min = self.get_property(obj_name, "min_hole_pos")
                position_max = self.get_property(obj_name, "max_hole_pos")

                table = Table()
                count = 0
                for rib_no in ribs:
                    raise NotImplementedError()
                    attachment_points = parametric_glider.lineset.get_upper_nodes(rib_no)
                    count_this = 0
                    for attachment_point in attachment_points:
                        if attachment_point.rib_pos > position_min and attachment_point.rib_pos < position_max:
                             # "pos", "size", "width", "vertical_shift", "rotation"
                            table[rib_no+1, count_this*5+0] = attachment_point.rib_pos
                            table[rib_no+1, count_this*5+1] = hole_height
                            table[rib_no+1, count_this*5+2] = hole_width/hole_height
                            table[rib_no+1, count_this*5+3] = vertical_shift
                            table[rib_no+1, count_this*5+4] = rotation
                            count_this += 1
                            
                    count = max(count, count_this)
                
                for i in range(count):
                    table[0, 5*i] = "HOLE5"
                
                parametric_glider.tables.holes.table.append_right(table)
            
            else:
                logger.warning(classname)
        
    