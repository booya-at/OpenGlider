import numpy

def choose(int n, int k):
    if 0 <= k <= n:
        ntok = 1
        ktok = 1
        for t in xrange(1, min(k, n - k) + 1):
            ntok *= n
            ktok *= t
            n -= 1
        return ntok // ktok
    else:
        return 0

def bernsteinbase(int d, int n, double x):
    return choose(d - 1, n) * (x ** n) * ((1 - x) ** (d - 1 - n))

def get_bezier_point(ctrl_pts, double x):
    i_end = len(ctrl_pts)
    j_end = len(ctrl_pts[0])
    out_arr = numpy.zeros([j_end])
    for i in range(i_end):
        fac = bernsteinbase(i_end, i, x)
        for j in range(j_end):
            out_arr[j] += fac * ctrl_pts[i][j]

    return out_arr