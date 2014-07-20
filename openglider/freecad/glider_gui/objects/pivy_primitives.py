from pivy import coin

class line():
    def __init__(self, points=None):
        self.object = coin.SoSeparator()
        self.ls = coin.SoLineSet()
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.update(points)
        self.object.addChild(self.color)
        self.object.addChild(self.data)
        self.object.addChild(self.ls)

    def update(self, points):
        self.color.diffuseColor.setValue(0, 0, 0)
        self.data.point.setValue(0, 0, 0)
        self.data.point.setValues(0, len(points), points)