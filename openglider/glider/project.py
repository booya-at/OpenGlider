import os
import re
import datetime
import logging

from openglider.glider.glider import Glider
from openglider.glider.parametric import ParametricGlider
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
        self.name = name
        self.modified = modified or datetime.datetime.now()

        self.setup()

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
        table["A9"] = "Attachment point z"

        z = self.glider_3d.lineset.get_main_attachment_point().vec[2]
        table["B9"] = f"{z:.03f}"
        table["A10"] = "Att. z (relative to span)"
        z_rel = z / self.glider.shape.span * 100
        table["B10"] = f"{z_rel:.01f} %"

        return table

    def save(self, filename):
        if filename.endswith(".ods"):
            self.glider.export_ods(filename)
        elif filename.endswith(".json"):
            openglider.save(self, filename)
        else:
            raise ValueError("Invalid Extension ({})".format(filename))
        
        self.filename = filename

    def setup(self):
        #self.name = self.glider.name
        if self.filename is not None:
            self.name = os.path.split(self.filename)[1]

    def copy(self):
        new_glider = self.glider.copy()
        new_glider_3d = self.glider_3d.copy()
        new = GliderProject(new_glider, new_glider_3d)
        new.name = self.name

        return new

    @classmethod
    def import_ods(cls, path):
        glider_2d = ParametricGlider.import_ods(path)

        return cls(glider_2d)

    def update_all(self):
        self.glider.get_glider_3d(self.glider_3d)
        self.glider_3d.lineset.recalc()

    def __json__(self):
        return {"glider": self.glider,
                "glider_3d": self.glider_3d,
                "name": self.name,
                "modified": self.modified
                }

    def get_data(self):
        area = self.glider_3d.area
        area_projected = self.glider_3d.projected_area
        return {
            "area": area,
            "area_projected": area_projected,
            "flattening": (1.-area_projected/area) * 100,
            "aspect_ratio": self.glider_3d.aspect_ratio
        }
