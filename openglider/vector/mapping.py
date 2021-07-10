from typing import List, Tuple

import math
import numpy
import euklid
import openglider.jsonify

d = 1e-5

class Quad:
    # arbitrary quadrilateral interpolation
    # barycentric coordinates
    # https://numfactory.upc.edu/web/FiniteElements/Pract/P4-QuadInterpolation/html/QuadInterpolation.html
    matrix: numpy.matrix = numpy.matrix([
        [1,0,0,0],
        [1,1,0,0],
        [1,1,1,1],
        [1,0,1,0]
    ])

    matrix_inverse: numpy.matrix = numpy.linalg.inv(matrix)

    def __init__(self, p1, p2, p3, p4):
        self.nodes = [
            p1, p2, p3, p4
        ]

        self.a = list(self.matrix_inverse.dot([p[0] for p in self.nodes]).flat)
        self.b = list(self.matrix_inverse.dot([p[1] for p in self.nodes]).flat)


    def to_global(self, l, m) -> euklid.vector.Vector2D:
        x = self.a[0] + l*self.a[1] + m*self.a[2] + self.a[3]*l*m
        y = self.b[0] + l*self.b[1] + m*self.b[2] + self.b[3]*l*m
        
        return euklid.vector.Vector2D([x,y])

    def to_local(self, point: euklid.vector.Vector2D) -> Tuple[float, float]:
        a = self.a[3]*self.b[2] - self.a[2]*self.b[3]
        b = self.a[3]*self.b[0] - self.a[0]*self.b[3] + self.a[1]*self.b[2] - self.a[2]*self.b[1] + self.b[3]*point[0] - self.a[3]*point[1]
        c = self.a[1]*self.b[0] - self.a[0]*self.b[1] + self.b[1]*point[0] - self.a[1]*point[1]
        
        if abs(a) < 1e-10:
            m = -c/b
            l = m
        else:
            m = (-b + math.sqrt(b**2 - 4*a*c))/(2*a)
            l = (point[0] - self.a[0] - self.a[2]*m) / (self.a[1] + self.a[3]*m)

        return l, m


class Mapping:
    def __init__(self, curves: List[euklid.vector.PolyLine2D]):
        self.curves = curves
        self.curve_length = len(curves[0].nodes)

        for curve in curves:
            if len(curve.nodes) != self.curve_length:
                raise Exception()
        

        self.quad_map = {}
        self.quads = []

        for curve_index in range(len(self.curves)-1):
            quads = []
            for node_index in range(len(curve.nodes)-1):
                quad =Quad(
                    self.curves[curve_index].nodes[node_index],
                    self.curves[curve_index].nodes[node_index+1],
                    self.curves[curve_index+1].nodes[node_index+1],
                    self.curves[curve_index+1].nodes[node_index],
                )

                quads.append(quad)
                self.quad_map[quad] = (curve_index, node_index)
            
            self.quads.append(quads)
    
    def __json__(self):
        return {
            "curves": self.curves
        }

    def get_point(self, ik_x, ik_y) -> euklid.vector.Vector2D:
        i_y = int(ik_y)
        k_y = ik_y-i_y

        i_x = int(ik_x)
        if i_x >= len(self.quads[0]):
            i_x = len(self.quads[0])-1
        k_x = ik_x - i_x

        poly = self.quads[i_y][i_x]

        return poly.to_global(k_x, k_y)

    
    def get_iks(self, point: euklid.vector.Vector2D) -> Tuple[float, float]:
        min_distance = float("inf")
        for quads_row in self.quads:
            for quad in quads_row:
                m, l = quad.to_local(point)

                distance = max([
                    min([abs(m), abs(m-1)]),
                    min([abs(l), abs(l-1)])
                ])

                min_distance = min(min_distance, distance)
                

                if distance < 1+d:
                    offset_i, offset_x = self.quad_map[quad]

                    return offset_x + m, offset_i + l
        
        with open("/tmp/data.json", "w") as outfile:
            openglider.jsonify.dump([self, point], outfile)


class Mapping3D:
    def __init__(self, curves):
        self.curves = curves

    def get_point(self, ik_x, ik_y) -> euklid.vector.Vector3D:
        i_y = int(ik_y)
        if i_y >= len(self.curves)-1:
            i_y = len(self.curves)-2
            
        k_y = ik_y-i_y


        p1 = self.curves[i_y].get(ik_x)
        p2 = self.curves[i_y+1].get(ik_x)

        return p1 + (p2-p1) * k_y


if __name__ == "__main__":
    with open("/tmp/data.json") as infile:  
        mapping, node = openglider.jsonify.load(infile)["data"]
    
    mapping.get_iks(euklid.vector.Vector2D(node))