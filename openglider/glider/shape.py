from openglider.vector.drawing import PlotPart, Layout
from openglider.vector import PolyLine2D, norm

from openglider_cpp import euklid

class Shape(object):
    def __init__(self, front, back):
        if not isinstance(front, euklid.PolyLine2D):
            front = euklid.PolyLine2D(list(front))
        if not isinstance(back, euklid.PolyLine2D):
            back = euklid.PolyLine2D(list(back))
        self.front = front
        self.back = back

    def get_point(self, x, y):
        front = self.front.get(x)
        back = self.back(x)

        return front + (back-front) *  y

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
    def rib_no(self):
        return len(self.front)

    @property
    def ribs(self):
        return [[self.front.get(x), self.back.get(x)] for x in range(len(self.front))]

    @property
    def ribs_front_back(self):
        return [self.ribs, self.front, self.back]

    @property
    def span(self):
        return

    @property
    def chords(self):
        return [norm(p1-p2) for p1, p2 in zip(self.front, self.back)]

    @property
    def cell_widths(self):
        return [p2[0]-p1[0] for p1, p2 in zip(self.front.nodes[:-1], self.front.nodes[1:])]

    @property
    def area(self):
        front, back = self.front, self.back
        area = 0
        for i in range(len(self.front) - 1):
            l = (front.get(i)[1] - back.get(i)[1]) + (front.get(i+1)[1] - back.get(i+1)[1])
            area += l * (front.get(i+1)[0] - front.get(i)[0]) / 2
        return area

    def scale(self, x=1, y=1):
        self.front = self.front.scale(x, y)
        self.bak = self.back.scale(x, y)

        return self

    def copy_complete(self):
        front = self.front.mirror([0, 0], [0, 1]).reverse()
        back = self.back.mirror([0, 0], [0, 1]).reverse()

        if front.nodes[-1][0] == 0:
            front.nodes += self.front.copy().nodes[1:]
            back.nodes += self.back.copy().nodes[1:]

        return Shape(front, back)

    def _repr_svg_(self):
        da = Layout()
        for cell_no in range(self.cell_no):
            points = [
                self.get_point(cell_no, 0),
                self.get_point(cell_no, 1),
                self.get_point(cell_no+1, 1),
                self.get_point(cell_no+1, 0)
            ]
            points.append(points[0])
            da.parts.append(PlotPart(marks=[points]))

        return da._repr_svg_()

