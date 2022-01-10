import os
import re
import datetime
import logging
from typing import List, Tuple

import euklid

from openglider.glider.glider import Glider
from openglider.glider.parametric import ParametricGlider
from openglider.glider.parametric.import_freecad import import_freecad
from openglider.utils.dataclass import dataclass, field
import openglider.utils.table

logger = logging.getLogger(__name__)


@dataclass
class GliderProject(object):
    glider: ParametricGlider
    glider_3d: Glider=None
    filename: str=""
    name: str=None
    changelog: List[Tuple[datetime.datetime, str, str]]=field(default_factory=lambda: [])

    _regex_revision_no = re.compile(r"(.*)_rev([0-9]*)$")
    
    def __post_init__(self):
        if self.name is None:
            if self.filename is not None:
                self.name = os.path.split(self.filename)[1]
            else:
                self.name = "unnamed_project"

        if self.glider_3d is None:
            logger.info(f"get glider 3d:  {self.name}")
            self.glider_3d = self.glider.get_glider_3d()

        if len(self.changelog) < 1:
            self.changelog.append([
                datetime.datetime.now(), "loaded", "no changelog data available"
            ])
    
    @classmethod
    def __from_json__(cls, **kwargs):
        changelog = kwargs["changelog"]
        changelog_new = []
        for dt_str, value1, value2 in changelog:
            dt = datetime.datetime.fromisoformat(dt_str)

            changelog_new.append((dt, value1, value2))

        kwargs["changelog"] = changelog_new

        return cls(**kwargs)
            
        

    
    @property
    def modified(self):
        return self.changelog[-1][0]

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

        return self.name

    def get_data_table(self):
        table = openglider.utils.table.Table()
        table["A1"] = "Name"
        table["B1"] = f"{self.name}"
        table["A2"] = "Modified"
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

    def get_data(self):
        area = self.glider_3d.area
        area_projected = self.glider_3d.projected_area
        return {
            "area": area,
            "area_projected": area_projected,
            "flattening": (1.-area_projected/area) * 100,
            "aspect_ratio": self.glider_3d.aspect_ratio
        }
