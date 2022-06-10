from typing import List, Dict
import logging

import euklid

from openglider.lines.node import Node
from openglider.lines import line_types
from openglider.utils.cache import cached_property, CachedObject
from openglider.mesh import Mesh, Vertex, Polygon

logger = logging.getLogger(__name__)


class Line(CachedObject):
    rho_air = 1.2


    def __init__(self, lower_node, upper_node, v_inf,
                 line_type=line_types.LineType.get('default'), target_length=None, number=None, name=None, color=""):
        """
        Line Class
        """
        self.number = number
        self.type = line_type  # type of line
        self.v_inf = v_inf  # free-stream velocity
        
        self._color = None
        self.color = color

        self.lower_node = lower_node
        self.upper_node = upper_node

        self.target_length = target_length
        self.init_length = target_length

        self.force = None

        self.sag_par_1 = None
        self.sag_par_2 = None

        self.name = name or "unnamed_line"

    def __json__(self):
        return{
            'number': self.number,
            'lower_node': self.lower_node,
            'upper_node': self.upper_node,
            'v_inf': None,               # remove this!
            'line_type': self.type.name,
            'target_length': self.target_length,
            'name': self.name
        }

    @classmethod
    def __from_json__(cls, number, lower_node, upper_node, v_inf, line_type, target_length, name):
        return cls(lower_node,
                   upper_node,
                   v_inf,
                   line_types.LineType.get(line_type),
                   target_length,
                   number,
                   name)

    @property
    def color(self):
        return self._color or "default"

    @color.setter
    def color(self, color):
        if color in self.type.colors:
            self._color = color

    @property
    def has_geo(self):
        """
        true if upper and lower nodes of the line were already computed
        """
        #the node vectors can be None or numpy.arrays. So we have to check for both types
        try:
            return all(list(self.lower_node.vec) + 
                       list(self.upper_node.vec))
        except TypeError:
            # one of the nodes vec is None
            return False

    @property
    def v_inf_0(self):
        return self.v_inf.normalized()

    #@cached_property('lower_node.vec', 'upper_node.vec')
    @property
    def diff_vector(self):
        """
        Line Direction vector (normalized)
        :return:
        """
        return (self.upper_node.vec - self.lower_node.vec).normalized()

    #@cached_property('lower_node.vec', 'upper_node.vec')
    @property
    def diff_vector_projected(self):
        return (self.upper_node.vec_proj - self.lower_node.vec_proj).normalized()

    @cached_property('lower_node.vec', 'upper_node.vec', 'v_inf')
    def length_projected(self):
        return (self.lower_node.vec_proj - self.upper_node.vec_proj).length()

    @property
    def length_no_sag(self):
        return (self.upper_node.vec - self.lower_node.vec).length()

    @cached_property('lower_node.vec', 'upper_node.vec', 'v_inf', 'sag_par_1', 'sag_par_2')
    def length_with_sag(self):
        if self.sag_par_1 is None or self.sag_par_2 is None:
            raise ValueError('Sag not yet calculated!')

        return euklid.vector.PolyLine3D(self.get_line_points(numpoints=100)).get_length()

    def get_stretched_length(self, pre_load=50, sag=True):
        """
        Get the total line-length for production using a given stretch
        length = len_0 * (1 + stretch*force)
        """
        if sag:
            l_0 = self.length_with_sag
        else:
            l_0 = self.length_no_sag
        factor = self.type.get_stretch_factor(pre_load) / self.type.get_stretch_factor(self.force)
        return l_0 * factor

    #@cached_property('v_inf', 'type.cw', 'type.thickness')
    @property
    def ortho_pressure(self):
        """
        drag per meter (projected)
        :return: 1/2 * cw * d * v^2
        """
        return 1 / 2 * self.type.cw * self.type.thickness * self.rho_air * self.v_inf.dot(self.v_inf)

    #@cached_property('lower_node.vec', 'upper_node.vec', 'v_inf')
    @property
    def drag_total(self):
        """
        Get total drag of line
        :return: 1/2 * cw * A * v^2
        """
        drag = self.ortho_pressure * self.length_projected
        return drag

    def get_weight(self):
        if self.type.weight is None:
            logger.warning("predicting weight of linetype {self.type.name} by line-thickness.")
            logger.warning("Please enter line_weight in openglider/lines/line_types")
            weight = self.type.predict_weight()
        else:
            weight = self.type.weight
        try:
            return weight * self.length_with_sag
        except ValueError:
            # computing weight without sag
            return weight * self.length_no_sag

    @cached_property('force', 'lower_node.vec', 'upper_node.vec')
    def force_projected(self):
        try:
            return self.force * self.length_projected / self.length_no_sag
        except:
            raise Exception(f"invalid force: {self.name}, {self.force}")

    def get_line_points(self, sag=True, numpoints=10):
        """
        Return points of the line
        """
        if self.sag_par_1 is None or self.sag_par_2 is None:
            sag=False
        return [self.get_line_point(i / (numpoints - 1), sag=sag) for i in range(numpoints)]

    def get_line_point(self, x, sag=True):
        """pos(x) [x,y,z], x: [0,1]"""
        point = self.lower_node.vec * (1. - x) + self.upper_node.vec * x
        if sag:
            return point + self.v_inf_0 * self.get_sag(x)

        return point

    def get_sag(self, x):
        """sag u(x) [m], x: [0,1]"""
        xi = x * self.length_projected
        u = (- xi ** 2 / 2 * self.ortho_pressure /
             self.force_projected + xi *
             self.sag_par_1 + self.sag_par_2)
        return float(u)

    def get_mesh(self, numpoints=2, segment_length=None):
        if segment_length is not None:
            numpoints = max(round(self.length_no_sag / segment_length), 2)

        line_points = [Vertex(*point) for point in self.get_line_points(numpoints=numpoints)]
        boundary: Dict[str, List[Vertex]] = {"lines": []}
        if self.lower_node.type == Node.NODE_TYPE.LOWER:
            boundary["lower_attachment_points"] = [line_points[0]]
        else:
            boundary["lines"].append(line_points[0])
        if self.upper_node.type == Node.NODE_TYPE.UPPER:
            boundary["attachment_points"] = [line_points[-1]]
        else:
            boundary["lines"].append(line_points[-1])
        
        spring = self.type.get_spring_constant()
        stretch_factor = 1 + self.force / spring
        attributes = {
            "name": self.name,
            "l_12": self.length_no_sag / stretch_factor / (numpoints-1),
            "e_module": spring,
            "e_module_push": 0,
            "density": max(0.0001, (self.type.weight or 0)/1000)  # g/m -> kg/m, min: 0,1g/m
        }


        line_poly = {
            "lines": [
                Polygon(line_points[i:i + 2], attributes=attributes)
                for i in range(len(line_points) - 1)
                ]}

        return Mesh(line_poly, boundary)

    @property
    def _get_projected_par(self):
        c1_n = self.lower_node.get_diff().dot(self.v_inf_0)
        c2_n = self.upper_node.get_diff().dot(self.v_inf_0)
        return [c1_n + self.sag_par_1, c2_n / self.length_projected + self.sag_par_2]

    def get_connected_ribs(self, glider):
        '''
        return the connected ribs
        '''
        lineset = glider.lineset
        att_pnts = lineset.get_upper_influence_nodes(self)
        return set([att_pnt.rib for att_pnt in att_pnts])

    def get_rib_normal(self, glider):
        '''
        return the rib normal of the connected rib(s)
        '''
        ribs = self.get_connected_ribs(glider)
        result = euklid.vector.Vector3D()

        for rib in ribs:
            result += rib.normalized_normale

        return result.normalized()

    def rib_line_norm(self, glider):
        '''
        returns the squared norm of the cross-product of
        the line direction and the normal-direction of
        the connected rib(s)
        '''
        return self.diff_vector.dot(self.get_rib_normal(glider))

    def get_correction_influence(self, residual_force):
        '''
        returns an influence factor [force / length] which is a proposal for
        the correction of a residual force if the line is moved in the direction
        of the residual force
        '''
        diff = self.diff_vector
        l = diff.length()
        r = residual_force.length()
        
        normed_residual_force = residual_force / r
        normed_diff_vector = diff / l
        f = 1. - normed_residual_force.dot(normed_diff_vector)   # 1 if normal, 0 if parallel
        return f * self.force / l
