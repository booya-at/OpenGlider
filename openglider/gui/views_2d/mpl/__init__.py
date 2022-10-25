import numpy

import openglider.glider
from openglider.gui.views_2d.mpl.canvas import PlotCanvas


class InterpolationPlot(PlotCanvas):
    def plot(self, interpolation, cp, ballooning=None):
        x = interpolation.x
        start = min(x)
        end = max(x)

        x_values = numpy.linspace(start, end, 100)
        y_values = interpolation(x_values)
        y_cp = [-10*x for x in cp(x_values)]
        #self.axes.update({})
        self.axes.clear()
        self.axes.plot(x_values, y_values, "-")
        self.axes.plot(x_values, y_cp, "-", color="red")

        if ballooning:
            y_ballooning = [1000*ballooning[x] for x in x_values]
            self.axes.plot(x_values, y_ballooning, ".")
        self.axes.grid()

        self.draw()


class ShapePlot(PlotCanvas):
    def plot(self, glider):
        shape = glider.shape.get_shape()
        front = numpy.array(shape.front)
        back = numpy.array(shape.back)
        self.axes.set_aspect(1)
        self.axes.axis("off")
        self.axes.plot(front[:, 0], front[:, 1], "-")
        self.axes.plot(back[:, 0], back[:, 1], "-")

        for rib in shape.ribs:
            x = (rib[0][0], rib[1][0])
            y = (rib[0][1], rib[1][1])
            self.axes.plot(x, y, "-", color="black")

        self.draw()


class TensionPlot(PlotCanvas):
    def __init__(self, ballooning_case):
        self.ballooning_case = ballooning_case
        super(TensionPlot, self).__init__()

    def plot(self):
        x = range(1, len(self.ballooning_case.glider.cells)+1)
        ballooning_tensions = self.ballooning_case.get_tension_forces()
        cell_tensions = self.ballooning_case._get_cell_forces()

        self.axes.clear()

        self.axes.plot(x, ballooning_tensions, label="Tension Force (Ballooning)")
        self.axes.plot(x, cell_tensions, label="Cell Force (Arc)")
        self.axes.legend()
        self.axes.set_xlabel("cell-number")
        self.axes.set_ylabel("forces [N]")

        self.axes.grid()

        self.draw()
