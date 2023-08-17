from __future__ import annotations

from enum import Enum
import logging
import math
from typing import TYPE_CHECKING, Any

import euklid
from openglider.airfoil.profile_3d import Profile3D
import openglider.mesh as mesh
from openglider.airfoil import get_x_value
from openglider.materials import Material, cloth
from openglider.mesh.mesh import Vertex
from openglider.utils.cache import cached_function, hash_list
from openglider.utils.dataclass import BaseModel, Field
from openglider.vector.unit import Length, Percentage

if TYPE_CHECKING:
    from openglider.glider.cell.cell import Cell


logger = logging.getLogger(__name__)

class PANELCUT_TYPES(Enum):
    folded = 1
    orthogonal = 2
    cut_3d = 3
    singleskin = 4
    parallel = 5
    round = 6


class PanelCut(BaseModel):
    x_left: Percentage
    x_right: Percentage
    cut_type: PANELCUT_TYPES
    cut_3d_amount: list[float] = Field(default_factory=lambda: [0, 0])
    x_center: Percentage | None = None
    seam_allowance: Length | None = None

    def __json__(self) -> dict[str, Any]:
        return {
            "x_left": self.x_left,
            "x_right": self.x_right,
            "x_center": self.x_center,
            "cut_type": self.cut_type.name,
            "cut_3d_amount": self.cut_3d_amount,
            "seam_allowance": self.seam_allowance
        }

    @classmethod    
    def __from_json__(cls, **dct: Any) -> PanelCut:
        cut_type = getattr(PANELCUT_TYPES, dct["cut_type"])
        dct.update({
            "cut_type": cut_type
        })

        return cls(**dct)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PanelCut):
            return NotImplemented

        if self.x_left != other.x_left:
            return False
        
        if self.x_right != other.x_right:
            return False
        
        if self.cut_type != other.cut_type:
            return False
        
        if self.x_center != other.x_center:
            return False
        
        return True
    
    def mirror(self) -> None:
        self.x_left, self.x_right = self.x_right, self.x_left
    
    def get_x_values(self) -> list[Percentage]:
        values = [self.x_left, self.x_right]

        if self.x_center is not None:
            values.insert(1, self.x_center)
        
        return values
    
    def get_average_x(self) -> Percentage:
        values = self.get_x_values()
        
        return sum(values, start=Percentage(0))/len(values)
    
    def __hash__(self) -> int:
        return hash_list(self.x_left, self.x_right, self.cut_type)

    @cached_function("self")
    def _get_ik_values(self, cell: Cell, numribs: int=0, exact: bool=True) -> list[float]:
        x_values_left = cell.rib1.profile_2d.x_values
        x_values_right = cell.rib2.profile_2d.x_values

        ik_left = get_x_value(x_values_left, self.x_left)
        ik_right = get_x_value(x_values_right, self.x_right)

        points_2d = [
            euklid.vector.Vector2D([0, self.x_left]),
            euklid.vector.Vector2D([1, self.x_right])
        ]

        if self.x_center is not None:
            points_2d.insert(1, euklid.vector.Vector2D([0.5, self.x_center]))
            bspline = euklid.spline.BSplineCurve(points_2d).get_sequence(50)
            curve = euklid.vector.Interpolation(bspline.nodes)
        else:
            curve = euklid.vector.Interpolation(points_2d)
        
        ik_values = [ik_left]

        for i in range(1, numribs+1):
            x = i / (numribs+1)
            y = curve.get_value(x)

            _ik_left = get_x_value(x_values_left, y)
            _ik_right = get_x_value(x_values_right, y)
            ik_values.append(_ik_left + (_ik_right-_ik_left) * x)
        
        ik_values.append(ik_right)

        if not exact:
            return ik_values

        ik_values_new = []
        inner = cell.get_flattened_cell(num_inner=numribs+2).inner

        points_2d = [
            inner[0].get(ik_left),
            inner[-1].get(ik_right)
        ]

        if self.x_center:
            p = [0.5, self.x_center.si]
            p1 = inner[0].get(get_x_value(x_values_left, p[1]))
            p2 = inner[-1].get(get_x_value(x_values_left, p[1]))

            points_2d.insert(1, p1+(p2-p1)*p[0])
        
        if self.x_center:
            curve_exact = euklid.spline.BSplineCurve(points_2d).get_sequence(50)
        else:
            curve_exact = euklid.vector.PolyLine2D(points_2d)

        for i, ik in enumerate(ik_values):
            line: euklid.vector.PolyLine2D = inner[i]

            try:
                _ik, _ = line.cut(curve_exact, ik)
                if abs(_ik-ik) < 20:
                    ik = _ik
            except RuntimeError:
                logger.error(f"no cut found for panel: {self} ({i}/{ik})")

            ik_values_new.append(ik)
        
        return ik_values_new


    @cached_function("self")
    def _get_ik_interpolation(self, cell: Cell, numribs: int=0, exact: bool=True) -> euklid.vector.Interpolation:
        ik_values = self._get_ik_values(cell, numribs=5, exact=exact)
        numpoints = len(ik_values)-1
        ik_interpolation = euklid.vector.Interpolation(
            [[i/numpoints, x] for i, x in enumerate(ik_values)]
            )
        
        return ik_interpolation
    
    def get_curve_2d(self, cell: Cell, numribs: int=0, exact: bool=True) -> euklid.vector.PolyLine2D:
        ik_values = self._get_ik_values(cell, numribs=numribs, exact=exact)

        ribs = cell.get_flattened_cell(num_inner=numribs+2).inner
        points_2d = [rib.get(ik) for rib, ik in zip(ribs, ik_values)]

        return euklid.vector.PolyLine2D(points_2d)
    
    def get_curve_3d(self, cell: Cell, numribs: int=0, exact: bool=True) -> euklid.vector.PolyLine3D:
        ik_values = self._get_ik_values(cell, numribs, exact)

        ribs = cell.get_midribs(numribs+2)
        points = [rib.get(ik) for rib, ik in zip(ribs, ik_values)]

        return euklid.vector.PolyLine3D(points)


class Panel(BaseModel):
    """
    Glider cell-panel
    :param cut_front {'left': 0.06, 'right': 0.06, 'type': 'orthogonal'}
    """
    cut_front: PanelCut
    cut_back: PanelCut
    material: Material = cloth.get("porcher.skytex_32.white")
    name: str

    def __init__(self, cut_front: PanelCut, cut_back: PanelCut, material: Material | str | None=None, name: str="unnamed"):
        if isinstance(material, str):
            material = cloth.get(material)

        kwargs = {}
        if material is not None:
            kwargs["material"] = material
        
        # TODO: investigate type bug
        super().__init__(  # type: ignore
            cut_front=cut_front,
            cut_back=cut_back,
            name=name,
            **kwargs
        )

    def __json__(self) -> dict[str, Any]:
        return {'cut_front': self.cut_front,
                'cut_back': self.cut_back,
                "material": str(self.material),
                "name": self.name
                }

    @classmethod
    def dummy(cls) -> Panel:
        top = Percentage(-1)
        bottom = Percentage(1)
        return cls(
            PanelCut(
                x_left=top,
                x_right=top,
                cut_type=PANELCUT_TYPES.parallel
                ),
            PanelCut(
                x_left=bottom,
                x_right=bottom,
                cut_type=PANELCUT_TYPES.parallel
                )
        )
    
    def __hash__(self) -> int:
        return hash_list(self.cut_front.__hash__(), self.cut_back.__hash__())

    def mean_x(self) -> Percentage:
        """
        :return: center point of the panel as x-values
        """
        total = self.cut_front.x_left
        total += self.cut_front.x_right
        total += self.cut_back.x_left
        total += self.cut_back.x_right

        return total/4

    def __radd__(self, other: Panel) -> Panel | None:
        """needed for sum(panels)"""
        if not isinstance(other, Panel):
            return self
        
        return None

    def __add__(self, other: Panel) -> Panel | None:
        if self.cut_front == other.cut_back:
            return Panel(other.cut_front, self.cut_back, material=self.material)
        elif self.cut_back == other.cut_front:
            return Panel(self.cut_front, other.cut_back, material=self.material)
        else:
            return None

    def is_lower(self) -> bool:
        if (self.cut_front.x_left + self.cut_back.x_left) >=  1e-3:
            return True
        if (self.cut_front.x_right + self.cut_back.x_right) >=  1e-3:
            return True
        
        return False

    def get_3d(self, cell: Cell, numribs: int=0, midribs: list[Profile3D] | None=None) -> list[euklid.vector.PolyLine3D]:
        """
        Get 3d-Panel
        :param glider: glider class
        :param numribs: number of miniribs to calculate
        :return: List of rib-pieces (Vectorlist)
        """
        xvalues = cell.rib1.profile_2d.x_values
        ribs = []
        for i in range(numribs + 1):
            y = i / numribs

            if midribs is None:
                midrib = cell.midrib(y)
            else:
                midrib = midribs[i]

            x1 = self.cut_front.x_left + y * (self.cut_front.x_right -
                                               self.cut_front.x_left)
            front = get_x_value(xvalues, x1)

            x2 = self.cut_back.x_left + y * (self.cut_back.x_right -
                                              self.cut_back.x_left)
            back = get_x_value(xvalues, x2)
            ribs.append(midrib.get(front, back))
            # todo: return polygon-data
        return ribs

    def get_mesh(self, cell: Cell, numribs: int=0, exact: bool=False, tri: bool=False) -> mesh.Mesh:
        """
        Get Panel-mesh
        :param cell: the parent cell of the panel
        :param numribs: number of interpolation steps between ribs
        :return: mesh objects consisting of triangles and quadrangles
        """
        # TODO: doesn't work for numribs=0?
        
        xvalues = cell.rib1.profile_2d.x_values
        x_value_interpolation = euklid.vector.Interpolation([[i, x] for i, x in enumerate(xvalues)])

        rib_iks: list[list[float]] = []
        nodes: list[euklid.vector.Vector3D] = []
        rib_node_indices: list[list[int]] = []

        ik_values = self._get_ik_values(cell, numribs, exact=exact)

        for rib_no in range(numribs + 2):
            y = rib_no / max(numribs+1, 1)

            front, back = ik_values[rib_no]

            midrib = cell.midrib(y)

            rib_iks.append(midrib.get_positions(front, back))

            i0 = len(nodes)
            rib_node_indices.append([i + i0 for i, _ in enumerate(rib_iks[-1])])

            nodes += list(midrib.get(front, back))

        points = [mesh.Vertex(*p) for p in nodes]

        polygons = []
        lines: list[list[tuple[Vertex, Vertex]]] = []

        # helper functions
        def left_triangle(l_i: int, r_i: int) -> list[mesh.Polygon]:
            return [mesh.Polygon([points[l_i+1], points[l_i], points[r_i]])]

        def right_triangle(l_i: int, r_i: int) -> list[mesh.Polygon]:
            return [mesh.Polygon([points[r_i+1], points[l_i], points[r_i]])]

        def quad(l_i: int, r_i: int) -> list[mesh.Polygon]:
            if tri:
                return left_triangle(l_i, r_i) + right_triangle(l_i, r_i)
            else:
                return [mesh.Polygon([points[l_i+1], points[l_i], points[r_i], points[r_i+1]])]

        for rib_no, _ in enumerate(rib_iks[:-1]):
            x = (2*rib_no+1) / (numribs+1) / 2
            indices_left = rib_node_indices[rib_no]
            indices_right = rib_node_indices[rib_no + 1]

            iks_left = rib_iks[rib_no]
            iks_right = rib_iks[rib_no + 1]
            l_i = r_i = 0            

            while l_i < len(indices_left)-1 or r_i < len(indices_right)-1:
                if l_i == len(indices_left) - 1:
                    poly = right_triangle(indices_left[l_i], indices_right[r_i])
                    r_i += 1

                elif r_i == len(indices_right) - 1:
                    poly = left_triangle(indices_left[l_i], indices_right[r_i])
                    l_i += 1

                elif abs(iks_left[l_i] - iks_right[r_i]) == 0:
                    poly = quad(indices_left[l_i], indices_right[r_i])
                    r_i += 1
                    l_i += 1

                elif iks_left[l_i] <= iks_right[r_i]:
                    poly = left_triangle(indices_left[l_i], indices_right[r_i])
                    l_i += 1

                elif iks_right[r_i] < iks_left[l_i]:
                    poly = right_triangle(indices_left[l_i], indices_right[r_i])
                    r_i += 1

                # TODO: improve logic for triangles
                iks = [iks_left[l_i], iks_right[r_i]]
                if l_i < len(iks_left) - 1:
                    iks.append(iks_left[l_i+1])
                if r_i < len(iks_right) - 1:
                    iks.append(iks_right[r_i+1])
                
                for p in poly:
                    p.attributes["center"] = [x, x_value_interpolation.get_value(sum(iks)/len(iks))]

                polygons += poly

        mesh_data = {
            f"panel_{self.material}#{self.material.color_code}": polygons,
            }


        return mesh.Mesh(mesh_data, name=self.name)

    def mirror(self) -> Panel:
        """
        mirrors the cuts of the panel
        """
        self.cut_front.mirror()
        self.cut_back.mirror()
        return self
    
    def snap(self, cell: Cell) -> None:
        """
        replaces panel x_valus with x_values stored in profile-2d-x-values
        """
        p_l = cell.rib1.profile_2d
        p_r = cell.rib2.profile_2d
        self.cut_back.x_left = Percentage(p_l.find_nearest_x_value(self.cut_back.x_left.si))
        self.cut_back.x_right = Percentage(p_r.find_nearest_x_value(self.cut_back.x_right.si))
        self.cut_front.x_left = Percentage(p_l.find_nearest_x_value(self.cut_front.x_left.si))
        self.cut_front.x_right = Percentage(p_r.find_nearest_x_value(self.cut_front.x_right.si))

    @cached_function("self")
    def _get_ik_values(self, cell: Cell, numribs: int=0, exact: bool=True) -> list[tuple[float, float]]:
        """
        :param cell: the parent cell of the panel
        :param numribs: number of interpolation steps between ribs
        :return: [[front_ik_0, back_ik_0], ..[front_ik_n, back_ik_n]] with n is numribs + 1
        """
        ik_front = self.cut_front._get_ik_values(cell, numribs=numribs, exact=exact)
        ik_back = self.cut_back._get_ik_values(cell, numribs=numribs, exact=exact)

        return [(ik1, ik2) for ik1, ik2 in zip(ik_front, ik_back)]
        
    @cached_function("self")
    def _get_ik_interpolation(self, cell: Cell, numribs: int=0, exact: bool=True) -> tuple[euklid.vector.Interpolation, euklid.vector.Interpolation]:
        i1 = self.cut_front._get_ik_interpolation(cell, numribs, exact)
        i2 = self.cut_back._get_ik_interpolation(cell, numribs, exact)

        return i1, i2

    def integrate_3d_shaping(self, cell: Cell, sigma: float, inner_2d: list[euklid.vector.PolyLine2D], midribs: list[Profile3D] | None=None) -> tuple[list[float], list[float]]:
        """
        :param cell: the parent cell of the panel
        :param sigma: std-deviation parameter of gaussian distribution used to weight the length differences.
        :param inner_2d: list of 2D polylines (flat representation of the cell)s
        :param midribs: precomputed midribs, None by default
        :return: front, back (lists of lengths) with length equal to number of midribs
        """
        numribs = len(inner_2d) - 2
        if midribs is None or len(midribs) != len(inner_2d):
            ribs = cell.get_midribs(numribs+2)
        else:
            ribs = midribs

        positions = self._get_ik_values(cell, numribs, exact=True)

        front = []
        back = []

        ff = math.sqrt(math.pi/2)*sigma

        for rib_no in range(numribs + 2):
            x1, x2 = positions[rib_no]
            rib_2d = inner_2d[rib_no].get(x1,x2)
            rib_3d = ribs[rib_no].get(x1, x2)

            lengthes_2d = rib_2d.get_segment_lengthes()
            lengthes_3d = rib_3d.get_segment_lengthes()

            distance = 0.
            amount_front = 0.
            # influence factor: e^-(x^2/(2*sigma^2))
            # -> sigma = einflussfaktor [m]
            # integral = sqrt(pi/2)*sigma * [ erf(x / (sqrt(2)*sigma) ) ]

            def integrate(lengths_2d: list[float], lengths_3d: list[float]) -> float:
                amount = 0.
                distance = 0.

                for l2d, l3d in zip(lengths_2d, lengths_3d):
                    if l3d > 0:
                        factor = (l3d - l2d) / l3d
                        x = math.erf( (distance + l3d) / (sigma*math.sqrt(2))) - math.erf(distance / (sigma*math.sqrt(2)))

                        amount += factor * x
                    distance += l3d
            
                return amount

            amount_back = integrate(lengthes_2d, lengthes_3d)
            amount_front = integrate(lengthes_2d[::-1], lengthes_3d[::-1])

            for l2d, l3d in zip(lengthes_2d, lengthes_3d):
                if l3d > 0:
                    factor = (l3d - l2d) / l3d
                    x = math.erf( (distance + l3d) / (sigma*math.sqrt(2))) - math.erf(distance / (sigma*math.sqrt(2)))

                    amount_front += factor * x
                distance += l3d

            distance = 0
            amount_back = 0

            for l2d, l3d in zip(lengthes_2d[::-1], lengthes_3d[::-1]):
                if l3d > 0:
                    factor = (l3d - l2d) / l3d
                    x = math.erf( (distance + l3d) / (sigma*math.sqrt(2))) - math.erf(distance / (sigma*math.sqrt(2)))
                    amount_back += factor * x
                distance += l3d

            total = 0.
            for l2d, l3d in zip(lengthes_2d, lengthes_3d):
                total += l3d - l2d


            amount_front *= ff
            amount_back *= ff

            cut_3d_type = PANELCUT_TYPES.cut_3d

            if self.cut_front.cut_type != cut_3d_type and self.cut_back.cut_type != cut_3d_type:
                if abs(amount_front + amount_back) > abs(total):
                    normalization = abs(total / (amount_front + amount_back))
                    amount_front *= normalization
                    amount_back *= normalization

            if rib_no == 0 or rib_no == numribs+1:
                amount_front = 0.
                amount_back = 0.
                
            front.append(amount_front)
            back.append(amount_back)

        return front, back

#PanelCut.__pydantic_model__.update_forward_refs()  # type: ignore
