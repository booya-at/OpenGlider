from __future__ import division
import numpy
from copy import copy
from random import random

import openglider.vector as vector
from openglider.airfoil import Profile2D
import pyximport;
from openglider.vector.functions import norm, normalize

pyximport.install()
from openglider.airfoil.pan_2d_ext import C_douplet_const

numpy.set_printoptions(precision=3)
numpy.set_printoptions(suppress=True)


class panel_methode_2d():
    def __init__(self, airfoil, aoa=10. * numpy.pi, vel=10.,
        wake_numpoints=10, wake_length=1, wake_iteration=3):
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
        self.half_lenghts = []
        self.panel_normals = []
        self.panel_tangentials = []
        self.calc_panel_geo()
        self.create_mat_douplet_const()
        self.create_bc_vec()
        self.calc_douplet()

        for i in range(wake_iteration):
            self.recalc_wake()
            self.create_mat_douplet_const()
            self.calc_douplet()

        self.calc_velocity()
        self.calc_cp()

    def _douplet_const(self, point_j, panel):
        x1, y1 = panel[0]
        x2, y2 = panel[1]
        xj,yj = point_j
        return C_douplet_const(xj, yj, x1, y1, x2, y2)

    def create_mat_douplet_const(self):
        print("create douplet matrix")
        for i, mid in enumerate(self.panel_mids):
            for j, panel in enumerate(self.panel):
                d_0 = self._douplet_const(mid, panel)
                self.mat_douplet_cooef[i][j] = d_0
                if i == j:
                    self.mat_douplet_cooef[i][j] = 1 / 2
            for wake in self.wake_panels:
                d_0 = self._douplet_const(self.panel_mids[i], wake)
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
        for i in range(self.length):
            d0 = self.douplet[i]
            if i == 0:
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

    def global_velocity(self, point):
        dx = 0.
        dy = 0.
        x, y = point
        diff = 0.00000000000001
        for i, pan in enumerate(self.panel):
            dx += self.douplet[i] * (self._douplet_const([x + diff, y], pan) -
                self._douplet_const([x - diff, y], pan))
            dy += self.douplet[i] * (self._douplet_const([x, y + diff], pan) -
                self._douplet_const([x, y - diff], pan))
        for i, pan in enumerate(self.wake_panels):
            dx += (self.douplet[-1] - self.douplet[0]) * (
                self._douplet_const([x + diff, y], pan) -
                self._douplet_const([x - diff, y], pan))
            dy += (self.douplet[-1] - self.douplet[0]) * (
                self._douplet_const([x, y + diff], pan) -
                self._douplet_const([x, y - diff], pan))

        vx = numpy.array([dx / 2 / diff, dy / 2 / diff]) + self.v_inf.T[0]
        return vx

    def streamline(self, point=[0., 0.5], dist=0.1, steps=10, abbortx=6):
        p = numpy.array(point)
        stream = [copy(p)]
        for i in range(steps):
            vect = normalize(self.global_velocity(p))
            p += vect * dist
            stream.append(copy(p))
            if p[0] > abbortx:
                return stream
        return stream

    def potentialline(self, point=[0., 0.5], dist=0.1, steps=10):
        p = numpy.array(point)
        stream = [copy(p)]
        for i in range(steps):
            vect = normalize(self.global_velocity(p))
            vect = numpy.array([vect[1], -vect[0]])
            p += vect * dist
            stream.append(copy(p))
        return stream


    def inital_wake(self):
        for i in range(self.wake_numpoints):
            #self.wake[i][0] = 1 + i * self.wake_length / self.wake_numpoints
            # TODO: warum des? ( *self.aoa)
            #self.wake[i][1] = i * self.wake_length / self.wake_numpoints * self.aoa
            faktor = i*self.wake_length/self.wake_numpoints
            self.wake[i] = [1+faktor*numpy.cos(self.aoa), faktor*numpy.sin(self.aoa)]

    def recalc_wake(self):
        dist = self.wake_length / self.wake_numpoints
        steps = self.wake_numpoints
        self.wake = [[1,0]] + self.streamline(
            point = [1 + dist, 0. + random() * 0.001],
            dist=dist, steps=steps,
            abbortx=100)
        self.wake_panels = []
        for i in range(len(self.wake) - 1):
            self.wake_panels.append(numpy.array([self.wake[i], self.wake[i + 1]]))

    def calc_panel_geo(self):
        for i in range(self.length):
            self.panel.append(numpy.array([self.airfoil[i], self.airfoil[i + 1]]))
            self.panel_mids.append((self.airfoil[i] + self.airfoil[i + 1]) / 2)
            self.half_lenghts.append(norm(self.airfoil[i] - self.airfoil[i + 1]) / 2)
            self.panel_tangentials.append(self.panel[-1][1] - self.panel[-1][0])
            self.panel_normals.append(normalize([-self.panel_tangentials[-1][1], self.panel_tangentials[-1][0]]))
        for i in range(self.wake_numpoints - 1):
            self.wake_panels.append(numpy.array([self.wake[i], self.wake[i + 1]]))


#langsamer aber nicht viel
def _douplet_const(point_j, panel):
    point_i_1, point_i_2 = panel
    t = point_i_2 - point_i_1
    n_ = normalize([t[1], -t[0]])
    pn, s0 = numpy.linalg.solve(numpy.transpose(numpy.array([n_, t])), -point_i_1 + point_j)
    l = norm(t)
    if pn == 0:
        return (0)
    else:
        # print("pn: ", pn)
        # print("s0: ", s0)
        # print("l: ", l)
        return (1 / 2 / numpy.pi * (-numpy.arctan2(pn, (s0 - 1) * l) + numpy.arctan2(pn, s0 * l)))

def _c_douplet_const(point_j, panel):
    [x1, y1]= panel[0]
    [x2, y2]=panel[1]
    xj,yj = point_j
    return C_douplet_const(xj, yj, x1, y1, x2, y2)


def text_test():
    p1 = numpy.array([0, 0])
    p2 = numpy.array([0, 1])
    pj = numpy.array([1,0.01])
    # pan = panel_methode_2d([p1, p2, pj, p1], aoa=2 * numpy.pi / 180.)
    print(_douplet_const(pj, [p1, p2]))
    print(_c_douplet_const(pj, [p1, p2]))


def plot_test():
    arf = Profile2D.compute_naca(4412, numpoints=70)
    arf.close()
    arf.normalize()
    pan = panel_methode_2d(arf.data, aoa=7 * numpy.pi / 180, wake_length=2, wake_numpoints=50)
    print(pan.mat_douplet_cooef)
    from matplotlib import pyplot

    pyplot.plot(pan.douplet, marker="o")
    # pyplot.plot(pan.pressure, marker="x")
    # pyplot.plot(pan.pressure, marker="x")
    pyplot.show()


def graphics_test():
    from openglider.graphics import Graphics3D, Line

    arf = Profile2D.compute_naca(1010, numpoints=70)
    arf.close()
    arf.normalize()
    pan = panel_methode_2d(arf.data, aoa=20 * numpy.pi / 180, wake_length=3, wake_numpoints=50)
    arrows = []
    for i in range(pan.length):
        mid = pan.panel_mids[i]
        normal = pan.panel_normals[i]
        cp = pan.pressure[i]
        dip = pan.douplet[i]
        arrows.append([mid, mid + normal * cp / 30])
    arrows = numpy.array(arrows)
    stream = [pan.streamline(point=[-0.1, i], dist=0.01, steps=100) for i in numpy.linspace(-0.2,0.2,20)]
    # pot = [pan.potentialline(point=p, dist=0.02, steps=50) for p in pan.panel_mids[::5]]
    Graphics3D(
        # map(Line, pot) +
        map(Line, stream) + 
        map(Line, pan.panel) +
        # [Line(pan.airfoil)] + 
        # [Line(arrows[:, 1])]+
        #map(Line, arrows) +
        [Line(pan.wake)]
        )

from pylab import *
def visual_test_dipol(dup=_douplet_const):
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
            z[i][j] += dup([x[i], y[j]], panel1)
            z[i][j] -= dup([x[i], y[j]], panel2)
            z[i][j] += dup([x[i], y[j]], panel3)
            z[i][j] -= dup([x[i], y[j]], panel4)

    contourf(X, Y, z, levels = linspace(z.min(), z.max(), len(x)), ls = '-', cmap=cm.winter, origin="lower")
    show()

def visual_test_airfoil(num=70):

    arf = Profile2D.import_from_dat("../../tests/testprofile.dat")
    arf.numpoints = num
    pan = panel_methode_2d(arf.data, aoa=10 * numpy.pi / 180, wake_length=1.5, wake_numpoints=10)
    x = numpy.linspace(-0.3, 1.3, num)
    y = numpy.linspace(-0.2, 0.2, num)
    X, Y = meshgrid(x, y)
    z = numpy.zeros([len(x), len(y)])
    for i in range(len(z)):
        for j in range(len(z[0])):
            for k in range(len(pan.douplet)):
                z[i][j] += pan.douplet[k] * dup([x[j], y[i]], pan.panel[k])
            for k in range(len(pan.wake_panels)):
                z[i][j] -= (+pan.douplet[0] - pan.douplet[-1]) * dup([x[j], y[i]], pan.wake_panels[k])
            z[i][j] += dot([x[j], y[i]], pan.v_inf)

    contourf(X, Y, z, levels = linspace(z.min(), z.max(), len(x)), ls = '-', cmap=cm.winter, origin="lower")
    show()


if __name__ == "__main__":
    # text_test()
    plot_test()
    # graphics_test()
    # visual_test_dipol()
    # visual_test_airfoil()
