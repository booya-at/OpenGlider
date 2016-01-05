from openglider.plots.part import PlotPart, DrawingArea
from openglider.vector import PolyLine2D, norm


class Shape(object):
    def __init__(self, front, back):
        if not isinstance(front, PolyLine2D):
            front = PolyLine2D(front)
        if not isinstance(back, PolyLine2D):
            back = PolyLine2D(back)
        self.front = front
        self.back = back

    def get_point(self, x, y):
        front = self.front[x]
        back = self.back[x]

        return front + y * (back-front)

    def get_panel(self, cell_no, panel):
        p1 = self.get_point(cell_no, panel.cut_front["left"])
        p2 = self.get_point(cell_no, panel.cut_back["left"])
        p3 = self.get_point(cell_no+1, panel.cut_back["right"])
        p4 = self.get_point(cell_no+1, panel.cut_front["right"])

        return p1, p2, p3, p4

    @property
    def cell_no(self):
        return len(self.front) - 1

    @property
    def ribs(self):
        return list(zip(self.front.data.tolist(), self.back.data.tolist()))

    @property
    def ribs_front_back(self):
        return [self.ribs, self.front, self.back]

    @property
    def chords(self):
        return [norm(p1-p2) for p1, p2 in zip(self.front, self.back)]

    @property
    def area(self):
        front, back = self.front, self.back
        area = 0
        for i in range(len(self.front) - 1):
            l = (front[i][1] - back[i][1]) + (front[i+1][1] - back[i+1][1])
            area += l * (front[i+1][0] - front[i][0]) / 2
        return area

    def copy_complete(self):
        front = self.front.copy().mirror([0, 0], [0, 1])[::-1]
        back = self.back.copy().mirror([0, 0], [0, 1])[::-1]

        if front[-1][0] == 0:
            front = front[:-1]
            back = back[:-1]

        return Shape(front + self.front, back + self.back)

    def _repr_svg_(self):
        da = DrawingArea()
        for cell_no in range(self.cell_no):
            points = [
                self.get_point(cell_no, 0),
                self.get_point(cell_no, 1),
                self.get_point(cell_no+1, 1),
                self.get_point(cell_no+1, 0),
            ]
            points.append(points[0])
            da.parts.append(PlotPart(marks=[points]))

        return da._repr_svg_()


class ParametricShape(Shape):
    pass
