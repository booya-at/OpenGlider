from openglider.Vector import Vectorlist
import openglider.glider.cells


class DiagonalRib(object):
    def __init__(self, (left_1, left_1_height), (left_2, left_2_height),
                 (right_1, right_1_height), (right_2, right_2_height), cell_no):
        # Attributes
        self.attributes = [[[left_1, left_1_height], [left_2, left_2_height]],
                           [[right_1, right_1_height], [right_2, right_2_height]]]
        self.cell = cell_no

    def get_3d(self, glider):
        cell = glider.cells[self.cell]
        cell = openglider.glider.cells.Cell()
        lists = []
        for i, attributes in enumerate(self.attributes):
            points = [cell.ribs[i].profilepoint(x, h) for x, h in attributes]
            if attributes[0, 1] == attributes[1, 1] == 0:
                lists.append(cell.ribs[i].get(points[0, 1], points[1, 1]))
            else:
                lists.append(points)

        return lists

    def plot_3d(self, graphicsobject):
        pass  # ????

    def get_flattened(self, glider, ribs_flattened):
        first, second = self.get_3
        # Insert Marks into ribs
        # ribs_flattened[self.cell]
        # ribs_flattened[self.cell+1]


class TensionStrapSimple(DiagonalRib):
    def __init__(self, left, right, width, cell_no):
        super(TensionStrapSimple, self).__init__((left - width, 0), (left + width, 0),
                                                 (right - width, 0), (right + width, 0), cell_no)

    def get_flattened(self, glider, ribs_flattened):
        ## Draw signs into profile (just one)

        ## Return Lengths

        pass





