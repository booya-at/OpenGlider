import os
import re
import datetime
import logging

import euklid

from openglider.glider.glider import Glider
from openglider.glider.parametric import ParametricGlider
from openglider.glider.parametric.import_freecad import import_freecad
import openglider.utils.table

logger = logging.getLogger(__name__)

class GliderProject(object):
    glider: ParametricGlider
    glider_3d: Glider

    _regex_revision_no = re.compile(r"(.*)_rev([0-9]*)$")

    def __init__(self,
                 glider: ParametricGlider,
                 glider_3d: Glider = None,
                 filename: str = None,
                 name: str = None,
                 modified: datetime.datetime = None
                 ):
        self.glider = glider
        if glider_3d is None:
            logger.info(f"get glider 3d:  {name}")
            glider_3d = glider.get_glider_3d()

        self.glider_3d = glider_3d
        self.filename = filename
        self.modified = modified or datetime.datetime.now()

        if name is None:
            if self.filename is not None:
                name = os.path.split(self.filename)[1]
            else:
                name = "unnamed_project"
        
        self.name = name

    def increase_revision_nr(self):
        match = self._regex_revision_no.match(self.name)

        if match:
            name = match.group(1)
            revision_nr = int(match.group(2))
        else:
            name = self.name
            revision_nr = 0

        revision_nr += 1

        self.name = f"{name}_rev{revision_nr:03d}"
        self.modified = datetime.datetime.now()

        return self.name

    def get_data_table(self):
        table = openglider.utils.table.Table()
        table["A1"] = "Name"
        table["B1"] = f"{self.name}"
        table["A2"] = "Date"
        table["B2"] = self.modified.strftime("%d.%m.%Y")
        table["A3"] = "Time"
        table["B3"] = self.modified.strftime("%H:%M")
        table["A4"] = "Area"
        table["B4"] = f"{self.glider_3d.area:.02f} m²"
        table["A5"] = "Area projected"
        table["B5"] = f"{self.glider_3d.projected_area:.02f} m²"
        table["A6"] = "Aspect Ratio"
        table["B6"] = f"{self.glider_3d.aspect_ratio:.02f}"

        flattening = 100 * (1 - self.glider_3d.projected_area / self.glider_3d.area)
        table["A7"] = "Flattening"
        table["B7"] = f"{flattening:.01f} %"
        table["A8"] = "Cells"
        table["B8"] = str(self.glider.shape.cell_num)

        table["A9"] = "Attachment point x"
        table["A10"] = "Attachment point z"

        attachment_point = self.glider_3d.lineset.get_main_attachment_point().vec
        table["B9"] = f"{attachment_point[0]:.03f}"
        table["B10"] = f"{attachment_point[2]:.03f}"

        table["A11"] = "Att. z (relative to span)"
        z_rel = attachment_point[2] / self.glider.shape.span * 100
        table["B11"] = f"{z_rel:.01f} %"

        rib = self.glider_3d.ribs[0]
        p0 = rib.align([0, 0])
        
        diff = attachment_point - p0
        rib_diff = rib.align([1, 0])-p0

        x_rel = diff.dot(rib_diff) / rib_diff.dot(rib_diff) * 100

        table["A12"] = "Att. x (relative to chord)"
        table["B12"] = f"{x_rel:.01f} %"

        return table

    def save(self, filename):
        if filename.endswith(".ods"):
            self.glider.export_ods(filename)
        elif filename.endswith(".json"):
            openglider.save(self, filename)
        else:
            raise ValueError("Invalid Extension ({})".format(filename))
        
        self.filename = filename

    def copy(self):
        new_glider = self.glider.copy()
        new_glider_3d = self.glider_3d.copy()
        new = GliderProject(new_glider, new_glider_3d)
        new.name = self.name

        return new

    @classmethod
    def import_ods(cls, path):
        glider_2d = ParametricGlider.import_ods(path)
        filename = os.path.split(path)[-1]
        name, ext = os.path.splitext(filename)
        return cls(glider_2d, name=name)
    
    @classmethod
    def import_freecad(cls, path):
        glider_2d = import_freecad(path)
        filename = os.path.split(path)[-1]
        name, ext = os.path.splitext(filename)
        return cls(glider_2d, name=name)

    def update_all(self):
        self.glider.get_glider_3d(self.glider_3d)
        self.glider_3d.lineset.recalc()

    def __json__(self):
        return {"glider": self.glider,
                "glider_3d": self.glider_3d,
                "name": self.name,
                "filename": self.filename,
                "modified": self.modified
                }
    
    @classmethod
    def __from_json__(cls, **dct):
        dct["modified"] = datetime.datetime.fromisoformat(dct["modified"])
        return cls(**dct)

    def get_data(self):
        area = self.glider_3d.area
        area_projected = self.glider_3d.projected_area
        return {
            "area": area,
            "area_projected": area_projected,
            "flattening": (1.-area_projected/area) * 100,
            "aspect_ratio": self.glider_3d.aspect_ratio
        }
