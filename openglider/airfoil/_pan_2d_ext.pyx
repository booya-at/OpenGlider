import math

def C_douplet_const(double xj, double yj, double x1, double y1, double x2, double y2):
    cdef double tx, ty, rx, ry, l, pn, s0, out
    tx = x2 - x1
    ty = y2 - y1
    l = (tx ** 2 + ty ** 2) ** 0.5
    rx = xj - x1
    ry = yj - y1
    pn = (rx * ty - ry * tx) / l
    if pn == 0:
        out = 0.
        return out
    else:
        s0 = (rx * tx + ry * ty) / l ** 2
        # print("c_p0: ", pn)
        # print("c_s0: ", s0)
        # print("c_l: ", l)
        out = 1. / 2. / math.pi * (-math.atan2(pn, (s0 - 1.) * l) + math.atan2(pn, s0 * l))
        return out