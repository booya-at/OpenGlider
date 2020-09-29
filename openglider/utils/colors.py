from openglider.vector import Interpolation


def colorwheel(num):
    # r = 0
    # g = 1/3
    # b = 2/3
    colors = []
    for i in range(num):
        alpha = (i/num)
        red = max(0, 1 - 3*abs(alpha))
        green = max(0, 1 - 3*abs(1/3 - alpha))  # 1/3 -> 1, 0->0, 2/3->0
        blue = max(0, 1 - 3*abs(2/3 - alpha))

        rgb = [int(255*x) for x in (red, green, blue)]
        factor = 255 / max(rgb)
        rgb_normalized = [min(255, int(factor*x)) for x in rgb]
        colors.append(rgb_normalized)

    return colors

class HeatMap():
    _interpolation_red = Interpolation([
        [0, 0],
        [0.35, 0],
        [0.66, 1],
        [1, 1]
    ])

    _interpolation_blue = Interpolation([
        [0, 1],
        [0.34, 1],
        [0.65, 0],
        [1, 0]
    ])

    _interpolation_green = Interpolation([
        [0, 0],
        [0.125, 0],
        [0.375, 1],
        [0.64, 1],
        [0.91, 0],
        [1, 0]
    ])

    def __init__(self, min_value=0, max_value=100):
        self.min_value = min_value
        self.max_value = max_value

    @classmethod
    def from_data(cls, data):
        min_value = min(data)
        max_value = max(data)
        if abs(max_value - min_value) < 1e-5:
            max_value += 0.1
        return cls(min_value, max_value)
    
    def __call__(self, value):
        pct_raw = (value - self.min_value) / (self.max_value - self.min_value)
        pct = min(1., max(0, pct_raw))

        red = self._interpolation_red(pct)
        blue = self._interpolation_blue(pct)
        green = self._interpolation_green(pct)

        rgb = [int(255*x) for x in (red, green, blue)]

        return rgb