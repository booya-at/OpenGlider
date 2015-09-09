

class GliderProject():
    def __init__(self, glider2d, glider3d=None):
        self.glider2d = glider2d
        self.glider3d = glider3d or glider2d.get_glider_3d()

    def update_all(self):
        self.glider2d.get_glider_3d(self.glider3d)

    def __json__(self):
        return {"glider2d": self.glider2d,
                "glider3d": self.glider3d}

