import os
import re
import datetime

import openglider.glider.parametric
import openglider.glider.glider
import openglider.utils.table


class GliderProject(object):
    _regex_revision_no = re.compile(r"(.*)_rev([0-9]*)$")

    def __init__(self,
                 glider: openglider.glider.parametric.glider.ParametricGlider,
                 glider_3d: openglider.glider.glider.Glider = None,
                 filename: str = None,
                 name: str = "unnamed",
                 modified: datetime.datetime = None
                 ):
        self.glider = glider
        if glider_3d is None:
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

        self.name = "{}_rev{:03d}".format(name, revision_nr)
        self.modified = datetime.datetime.now()

        return self.name

    def get_data_table(self):
        table = openglider.utils.table.Table()
        table["A1"] = "Cells"
        table["B1"] = str(self.glider.shape.cell_num)
        table["A2"] = "Area"
        table["B2"] = "{:.02f} m²".format(self.glider_3d.area)
        table["A3"] = "Area projected"
        table["B3"] = "{:.02f} m²".format(self.glider_3d.projected_area)

        flattening = 100 * (1 - self.glider_3d.projected_area / self.glider_3d.area)
        table["A4"] = "Flattening"
        table["B4"] = "{:.01f} %".format(flattening)
        table["A5"] = "Aspect Ratio"
        table["B5"] = "{:.02f}".format(self.glider_3d.aspect_ratio)

        return table

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
        glider_2d = openglider.glider.parametric.ParametricGlider.import_ods(path)

        return cls(glider_2d)

    def update_all(self):
        self.glider.get_glider_3d(self.glider_3d)

    def __json__(self):
        return {"glider": self.glider,
                "glider_3d": self.glider_3d,
                "name": self.name,
                #"modified": self.modified
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
