from openglider.glider.parametric import ParametricGlider

class GliderProject(object):
    def __init__(self, glider2d, glider3d=None):
        self.glider2d = glider2d
        self.glider3d = glider3d or glider2d.get_glider_3d()

    @classmethod
    def import_ods(cls, path):
        glider_2d = ParametricGlider.import_ods(path)

        return cls(glider_2d)

    def update_all(self):
        self.glider2d.get_glider_3d(self.glider3d)

    def __json__(self):
        return {"glider2d": self.glider2d,
                "glider3d": self.glider3d}

    def get_data(self):
        area = self.glider3d.area
        area_projected = self.glider3d.projected_area
        return {
            "area": area,
            "area_projected": area_projected,
            "flattening": (1.-area_projected/area) * 100,
            "aspect_ratio": self.glider3d.aspect_ratio
        }

