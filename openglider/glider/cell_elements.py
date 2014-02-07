class DiagonalRib(object):
    def __init__(self, (left_1, left_1_height), (left_2, left_2_height),
                 (right_1, right_1_height), (right_2, right_2_height), cell_no):
        # Attributes
        self.attributes = [[[left_1, left_1_height], [left_2, left_2_height]],
                           [[right_1, right_1_height], [right_2, right_2_height]]]
        self.cell = cell_no

    def get_3d(self, glider):
        cell = glider.cells[self.cell]
        p1 = cell.prof1
        p2 = cell.prof2

        return False

    def get_flattened(self, glider, ribs_flattened):
        pass


class TensionStrapSimple(DiagonalRib):
    def __init__(self, left, right, width, cell_no):
        super(TensionStrapSimple, self).__init__((left - width, 0), (left + width, 0),
                                                 (right - width, 0), (right + width, 0), cell_no)

    def get_flattened(self, glider, ribs_flattened):
        ## Draw signs into profile

        ## Return Lengths

        pass





