from __future__ import division
import numpy as np


class JoukowskyAirfoil(object):
    '''the joukowsky airfoil is created by applieng the joukowsky transformation
       1 + 1 / z at a circle which passes 1 + 0j and has the center point in the
       second quatrant of the complex-plane.
       the joukowsky airfoil is used to get an analytic solution to the potential
       flow problem and is useful for the comparison to numeric methodes.'''

    def __init__(self, midpoint):
        self.midpoint = midpoint

    def circle(self, num=100):
        '''A circle with center midpoint and passing 0j + 1'''

        def circle_val(phi):
            return self.midpoint + self.radius * np.e ** ((phi - self.beta) * 1j)

        return np.array([circle_val(phi) for phi in np.linspace(0, 2 * np.pi, num)])

    @property
    def radius(self):
        return abs(1 - self.midpoint)

    @property
    def beta(self):
        '''the angle between 0j + 1, the midpoint and a horizontal line'''
        return np.arcsin(self.midpoint.imag / self.radius)

    def zeta(self, z):
        '''maps a complex number z to the zeta-plane'''
        return z + 1 / z

    def dz_dzeta(self, z):
        '''d_z / d_zeta'''
        dzeta_dz = (1 - 1 / z**2)
        return 1. if dzeta_dz == 0 else 1 / dzeta_dz

    def z(self, zeta):
        '''maps a complex number zeta to the z-plane'''
        z = (zeta + np.sqrt(zeta ** 2 - 4)) / 2
        # if the point is inside the object
        mid = self.midpoint.imag / (1 - self.midpoint.real) * 1j
        if abs(z - mid) < abs(mid + 1):
            z = (zeta - np.sqrt(zeta ** 2 - 4)) / 2
        return z

    def coordinates(self, num=100):
        '''maps the z-circle to the zeta-plane which results in a joukowsky airfoil'''
        return np.array(list(map(self.zeta, self.circle(num))))

    def gamma(self, alpha):
        '''return the strength of the circulation to satisfy the kutta-condition
           for a given angle of attack alpha'''
        return 4 * np.pi * self.radius * np.sin(alpha + self.beta)

    def potential(self, z, alpha):
        '''return the potential of any point in the complex z-plane for a given
           angle of attack alpha'''
        W_inf = np.e ** (-1j * alpha) * (z - self.midpoint)
        W_dip = self.radius ** 2 * np.e ** (1j * alpha) * (1 / (z - self.midpoint))
        W_vort = 1j * self.gamma(alpha) / 2 / np.pi * np.log(z - self.midpoint)
        return W_inf + W_dip + W_vort

    def z_velocity(self, z, alpha):
        '''return the complex velocity of any point in the complex z-plane for
           a given angle of attack alpha'''
        Q_inf = np.e ** (-1j * alpha)
        Q_dip = - self.radius ** 2 * np.e ** (1j * alpha) * (1 / ((z - self.midpoint) ** 2))
        Q_vort = 1j * self.gamma(alpha) / (2 * np.pi) / (z - self.midpoint)
        return (Q_inf + Q_dip + Q_vort)

    def velocity(self, z, alpha):
        '''return the complex velocity mapped to the zeta-plane of a point in the
           z-plane for a given angle of attack alpha'''
        min_size = 0.1 * 10 ** (-10)
        if z > 1 - min_size and z < 1  + min_size:
            return (np.e ** (-1j * alpha) * np.e ** (1j * 2 * self.beta) *
                   np.cos(alpha + self.beta) / self.radius)
        return self.z_velocity(z, alpha) * self.dz_dzeta(z)

    def surface_velocity(self, alpha, num=100):
        '''return the complex velocity for a given angle of attack alpha'''
        return np.array([self.velocity(z, alpha) for z in self.circle(num)])

    def surface_cp(self, alpha, num=100):
        '''return the presure coeficient cp on the surface of the airfoil
           for a given angle of attack alpha'''
        return [1 - (v.real ** 2 + v.imag ** 2) for v in self.surface_velocity(alpha, num)]

    def x(self, num=100):
        a = self.coordinates(num)
        return a.real


class VanDeVoorenAirfoil(JoukowskyAirfoil):
    def __init__(self, tau, epsilon, chord_length=2):
        self.tau = tau
        self.epsilon = epsilon
        self.chord_length = chord_length
        super(VanDeVoorenAirfoil, self).__init__(midpoint=0+0j)

    @property
    def k(self):
        '''SA p.138 6.66'''
        return 2 - self.tau / np.pi

    @property
    def radius(self):
        '''LSA p.138 (6.65)'''
        return 2 * self.chord_length * (1 + self.epsilon) ** (self.k - 1) * 2 ** (-self.k)

    def zeta(self, z):
        '''LSA p.137 (6.62)'''
        a = (z - self.radius) ** self.k
        b = (z - self.radius * self.epsilon) ** (self.k - 1)
        return a / b + self.chord_length

    def dz_dzeta(self, z):
        k = self.k
        e = self.epsilon
        a = self.radius
        dzeta_dz = k*(-a + z)**(-1 + k)*(-(a*e) + z)**(1 - k) +\
            ((1 - k)*(-a + z)**k)/(-(a*e) + z)**k
        dzeta_dz = 0.00000001 if dzeta_dz == 0 else dzeta_dz
        return 1 / dzeta_dz

    def z(self, zeta):
        '''not invertable'''
        pass


class TrefftzKuttaAirfoil(JoukowskyAirfoil):
    '''http://en.wikipedia.org/wiki/Joukowsky_transform
       3. Trefftz_transform'''

    def __init__(self, midpoint, tau):
        self.tau = tau
        super(TrefftzKuttaAirfoil, self).__init__(midpoint)

    @property
    def n(self):
        return 2 - self.tau / np.pi

    def zeta(self, z):
        n = self.n
        a = (1 + 1 / z) ** n
        b = (1 - 1 / z) ** n
        return n * (a + b) / (a - b)

    def dz_dzeta(self, z):
        n = self.n
        a = (1 + 1 / z) ** n
        b = (1 - 1 / z) ** n
        if z ** 2 == 1 or a - b == 0:
            return 0
        dzeta_dz = 4 * n ** 2 / (z ** 2 - 1) * (a * b) / (a - b) ** 2
        dzeta_dz = 0.00000001 if dzeta_dz == 0 else dzeta_dz
        return 1 / dzeta_dz

    def velocity(self, z, alpha):
        '''return the complex velocity mapped to the zeta-plane of a point in the
           z-plane for a given angle of attack alpha'''
        min_size = 0.1 * 10 ** (-10)
        return self.z_velocity(z, alpha) * self.dz_dzeta(z)

    def z(self, zeta):
        '''not invertable'''
        pass
