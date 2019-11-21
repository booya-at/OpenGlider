import os
import re
import datetime

import openglider.glider.parametric
import openglider.glider.glider


class GliderProject(object):
    _regex_revision_no = re.compile(r"(.*)_rev([0-9]*)$")

    def __init__(self,
                 glider: openglider.glider.parametric.glider.ParametricGlider,
                 glider_3d: openglider.glider.glider.Glider = None,
                 filename: str = None,
                 modified: datetime.datetime = None
                 ):
        self.glider = glider
        if glider_3d is None:
            glider_3d = glider.get_glider_3d()

        self.glider_3d = glider_3d
        self.filename = filename
        self.name = "unnamed"
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
        return {"glider2d": self.glider,
                "glider3d": self.glider_3d}

    def get_data(self):
        area = self.glider_3d.area
        area_projected = self.glider_3d.projected_area
        return {
            "area": area,
            "area_projected": area_projected,
            "flattening": (1.-area_projected/area) * 100,
            "aspect_ratio": self.glider_3d.aspect_ratio
        }
