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


_interpolation_red = Interpolation([
    [0, 0],
    [0.35, 0],
    [0.66, 1],
    [0.98, 1],
    [1, 0.5]
])

_interpolation_blue = Interpolation([
    [0, 0.5],
    [0.11, 1],
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


def heatmap(x):
    """
    x -> [0,1]
    return (r,g,b) [0,255]
    """
    red = _interpolation_red(x)
    blue = _interpolation_blue(x)
    green = _interpolation_green(x)

    rgb = [int(255*x) for x in (red, green, blue)]
    return rgb
