
class DiagonalRib(object):
    def __init__(self, (left_1, left_1_height), (left_2, left_2_height),
                 (right_1, right_1_height), (right_2, right_2_height), cell_no):
        # Attributes
        self.attributes = [[[left_1, left_1_height], [left_2, left_2_height]],
                           [[right_1, right_1_height], [right_2, right_2_height]]]
        self.cell = cell_no

    def get_3d(self, glider):
        cell = glider.cells[self.cell]
        # cell = openglider.glider.cells.Cell()
        lists = []
        for i, attributes in enumerate(self.attributes):
            rib = cell.ribs[i]
            points = [rib.profile_2d.profilepoint(x, h) for x, h in attributes]
            if attributes[0][1] == attributes[1][1] == -1:
                #print(points)
                lists.append(rib.profile_3d.get(points[0][0], points[1][0]))
            else:
                lists.append([rib.align([p[0], p[1], 0]) for p in points])
        return lists

    def get_flattened(self, glider, ribs_flattened):
        first, second = self.get_3d(glider)
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








