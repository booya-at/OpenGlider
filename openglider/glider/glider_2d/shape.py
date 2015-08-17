

class Shape():
    def __init__(self, front, back):
        self.front = front
        self.back = back

    def get_point(self, x, y):
        front = self.front[x]
        back = self.back[x]

        return front + y * (back-front)

    def get_panel(self, cell_no, panel):
        p1 = self.get_point(cell_no, panel.left_front[0])
        p2 = self.get_point(cell_no, panel.left_back[0])
        p3 = self.get_point(cell_no+1, panel.right_back[0])
        p4 = self.get_point(cell_no+1, panel.right_front[0])

        return p1, p2, p3, p4

    @property
    def ribs(self):
        return list(zip(self.front, self.back))

    @property
    def ribs_front_back(self):
        return [self.ribs, self.front, self.back]

    @property
    def area(self):
        front, back = self.front, self.back
        area = 0
        for i in range(len(self.front) - 1):
            l = (front[i][1] - back[i][1]) + (front[i+1][1] - back[i+1][1])
            area += l * (front[i+1][0] - front[i][0]) / 2
        return area
