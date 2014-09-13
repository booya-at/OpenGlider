from __future__ import division
import numpy

import openglider.vector as vector
from openglider.airfoil import Profile2D

numpy.set_printoptions(precision=3)
numpy.set_printoptions(suppress=True)


class panel_methode_2d():
    def __init__(self, airfoil, aoa=10. * numpy.pi, vel=10., wake_numpoints=10, wake_length=1):
        self.aoa = aoa
        self.airfoil = airfoil
        self.q_inf = vel
        self.v_inf = numpy.multiply(vel, [[numpy.cos(self.aoa)], [numpy.sin(self.aoa)]])
        self.length = len(self.airfoil) - 1
        self.mat_douplet_cooef = numpy.zeros([self.length, self.length])

        self.wake_length = wake_length
        self.wake_numpoints = wake_numpoints
        self.wake = numpy.zeros([wake_numpoints, 2])
        self.inital_wake()
        self.douplet = numpy.zeros(self.length)
        self.velocity = numpy.zeros(self.length)
        self.pressure = numpy.zeros(self.length)
        self.bc_vec = numpy.zeros(self.length)
        self.panel_mids = []
        self.panel = []
        self.wake_panels = []
        self.half_lenghts = numpy.zeros(self.length)
        self.panel_normals = []
        self.panel_tangentials = []

        self.calc_panel_geo()
        self.create_mat_douplet_const()
        self.create_bc_vec()
        self.calc_douplet()
        self.calc_velocity()
        self.calc_cp()


    def _douplet_const(self, point_j, panel):
        point_i_1, point_i_2 = panel
        t = point_i_2 - point_i_1
        n_ = vector.normalize([t[1], -t[0]])
        pn, s0 = numpy.linalg.solve(numpy.transpose(numpy.array([n_, t])), -point_i_1 + point_j)
        l = vector.norm(t)
        if pn == 0:
            return 0
        else:
            return 1 / 2 / numpy.pi * (-numpy.arctan2(pn, (s0 - 1) * l) + numpy.arctan2(pn, s0 * l))

    def create_mat_douplet_const(self):
        print("create douplet matrix")
        for i in range(self.length):
            for j in range(self.length):
                d_0 = self._douplet_const(self.panel_mids[i], self.panel[j])
                self.mat_douplet_cooef[i][j] = d_0
                if i == j:
                    self.mat_douplet_cooef[i][j] = 1 / 2
            for j in range(len(self.wake) - 1):
                wake_w = numpy.array([self.wake[j], self.wake[j + 1]])
                d_0 = self._douplet_const(self.panel_mids[i], wake_w)
                self.mat_douplet_cooef[i][0] -= d_0
                self.mat_douplet_cooef[i][-1] += d_0

    def create_bc_vec(self):
        for i in range(self.length):
            self.bc_vec[i] -= self.panel_mids[i][0] * self.v_inf[0] + self.panel_mids[i][1] * self.v_inf[1]

    def calc_douplet(self):
        print("solve the system")
        lsg = numpy.linalg.solve(self.mat_douplet_cooef, self.bc_vec)
        for i in range(self.length):
            self.douplet[i] = lsg[i]

    def calc_velocity(self):
        print("calculate velocity")
        print(len(self.douplet))
        for i in range(self.length):
            d0 = self.douplet[i]
            if i == 0:
                print(i)
                dp = self.douplet[2]
                dm = self.douplet[1]
                lm = +self.half_lenghts[0] + self.half_lenghts[1]
                lp = lm + self.half_lenghts[1] + self.half_lenghts[2]
            elif i == self.length - 1:
                dp = self.douplet[i - 1]
                dm = self.douplet[i - 2]
                lp = -self.half_lenghts[i] - self.half_lenghts[i - 1]
                lm = lp - self.half_lenghts[i - 1] - self.half_lenghts[i - 2]
            else:
                dp = self.douplet[i + 1]
                dm = self.douplet[i - 1]
                lm = -self.half_lenghts[i] - self.half_lenghts[i - 1]
                lp = self.half_lenghts[i] + self.half_lenghts[i + 1]
            self.velocity[i] = -(((d0 - dp) * lm ** 2 + (dm - d0) * lp ** 2) / (lm * (lm - lp) * lp))

    def calc_cp(self):
        print("calculate pressure")
        for i in range(self.length):
            self.pressure[i] = 1 - self.velocity[i] ** 2 / self.q_inf ** 2

    def inital_wake(self):
        for i in range(self.wake_numpoints):
            #self.wake[i][0] = 1 + i * self.wake_length / self.wake_numpoints
            # TODO: warum des? ( *self.aoa)
            #self.wake[i][1] = i * self.wake_length / self.wake_numpoints * self.aoa
            faktor = i*self.wake_length/self.wake_numpoints
            self.wake[i] = [1+faktor*numpy.cos(self.aoa), faktor*numpy.sin(self.aoa)]

    def calc_panel_geo(self):
        for i in range(self.length):
            self.panel.append(numpy.array([self.airfoil[i], self.airfoil[i + 1]]))
            self.panel_mids.append((self.airfoil[i] + self.airfoil[i + 1]) / 2)
            self.half_lenghts[i] = vector.norm(self.airfoil[i] - self.airfoil[i + 1]) / 2
            self.panel_tangentials.append(self.panel[-1][1] - self.panel[-1][0])
            self.panel_normals.append(vector.normalize([-self.panel_tangentials[-1][1], self.panel_tangentials[-1][0]]))
        for i in range(self.wake_numpoints - 1):
            self.wake_panels.append(numpy.array([self.wake[i], self.wake[i + 1]]))

def _douplet_const(point_j, panel):
    point_i_1, point_i_2 = panel
    t = point_i_2 - point_i_1
    n_ = vector.normalize([t[1], -t[0]])
    pn, s0 = numpy.linalg.solve(numpy.transpose(numpy.array([n_, t])), -point_i_1 + point_j)
    l = vector.norm(t)
    if pn == 0:
        return (0)
    else:
        return (1 / 2 / numpy.pi * (-numpy.arctan2(pn, (s0 - 1) * l) + numpy.arctan2(pn, s0 * l)))



def test():
    p1 = numpy.array([0, 0])
    p2 = numpy.array([1, 0])
    pj = numpy.array([5, 5])
    arf = Profile2D()
    # arf.importdat("../../tests/testprofile.dat")
    arf.compute_naca(2400)
    arf.numpoints = 30
    pan = panel_methode_2d([p1, p2, pj, p1], aoa=2 * numpy.pi / 180.)
    print(pan._douplet_const(pj, [p1, p2]))
    print(pan._douplet_lin(pj, [p1, p2]))
    print(pan._source_const(pj, [p1, p2]))


def plot_test():
    arf = Profile2D()
    arf.compute_naca(2420, numpoints=120)
    arf.numpoints = 100
    pan = panel_methode_2d(arf.data, aoa=5 * numpy.pi / 180, wake_length=5, wake_numpoints=10)
    print(pan.mat_douplet_cooef)
    from matplotlib import pyplot

    pyplot.plot(pan.douplet, marker="o")
    pyplot.plot(pan.velocity, marker="x")
    # pyplot.plot(pan.pressure, marker="x")
    pyplot.show()


def graphics_test():
    from openglider.graphics import Graphics2D, Line

    arf = Profile2D()
    arf.compute_naca(2420, numpoints=120)
    arf.close()
    arf.normalize()
    pan = panel_methode_2d(arf.data, aoa=10 * numpy.pi / 180, wake_length=5, wake_numpoints=10)
    arrows = []
    for i in range(pan.length):
        mid = pan.panel_mids[i]
        normal = pan.panel_normals[i]
        cp = pan.pressure[i]
        arrows.append([mid, mid + normal * cp * pan.half_lenghts[i] * 10])
    arrows = numpy.array(arrows)
    Graphics2D([Line(pan.airfoil), Line(arrows[:, 1])] + map(Line, arrows))

from pylab import *
def visual_test_dipol():
    panel1 = numpy.array([[-2, 0], [0, 2]])
    panel2 = numpy.array([[-0, -2], [2, 0]])
    panel3 = numpy.array([[-2, 0], [-0, -2]])
    panel4 = numpy.array([[0, 2], [2, 0]])
    x = numpy.linspace(-5, 5, 50)
    y = numpy.linspace(-5, 5, 50)
    X, Y = meshgrid(x, y)
    z = numpy.zeros([len(x),len(y)])
    for i in range(len(z)):
        for j in range(len(z[0])):
            z[i][j] += _douplet_const([x[i], y[j]], panel1)
            z[i][j] -= _douplet_const([x[i], y[j]], panel2)
            z[i][j] += _douplet_const([x[i], y[j]], panel3)
            z[i][j] -= _douplet_const([x[i], y[j]], panel4)

    contourf(X, Y, z, levels = linspace(z.min(), z.max(), len(x)), ls = '-', cmap=cm.winter, origin="lower")
    show()

def visual_test_airfoil():

    arf = Profile2D("../../tests/testprofile.dat")
    arf.numpoints = 30
    pan = panel_methode_2d(arf.data, aoa=10 * numpy.pi / 180, wake_length=5, wake_numpoints=10)
    x = numpy.linspace(-0.3, 1.3, 30)
    y = numpy.linspace(-0.2, 0.2, 30)
    X, Y = meshgrid(x, y)
    z = numpy.zeros([len(x), len(y)])
    for i in range(len(z)):
        for j in range(len(z[0])):
            for k in range(len(pan.douplet)):
                z[i][j] += -dot([x[j], y[i]], pan.v_inf)  + 100 * pan.douplet[k] * _douplet_const([x[j], y[i]], pan.panel[k])

    contourf(X, Y, z, levels = linspace(z.min(), z.max(), len(x)), ls = '-', cmap=cm.winter, origin="lower")
    show()

if __name__ == "__main__":
    # plot_test()
    # graphics_test()
    # visual_test_dipol()
    visual_test_airfoil()

# dot([x[j], y[i]], pan.v_inf)
