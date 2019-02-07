from openglider.vector import PolyLine2D


class Interpolation(PolyLine2D):
    def __init__(self, data, name=None, extrapolate=True):
        super(Interpolation, self).__init__(data, name)
        self.extrapolate = extrapolate

    def __call__(self, xval):
        last_point = self.data[0]
        for index, point in enumerate(self.data):
            if index == 0:
                continue

            lower_bound = self.extrapolate or last_point[0] < xval
            end_of_list = self.extrapolate and index == len(self.data) - 1

            if (lower_bound and xval < point[0]) or end_of_list:
                d_x = point[0] - last_point[0]
                return last_point[1] + (xval-last_point[0])/d_x * (point[1] - last_point[1])

            last_point = point

        raise Exception
