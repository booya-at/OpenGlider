from __future__ import annotations

import typing
import euklid

import openglider.airfoil
from openglider.utils.dataclass import dataclass
from openglider.glider.rib.rigidfoils import RigidFoilBase, RigidFoilCurved
from openglider.vector.unit import Percentage

if typing.TYPE_CHECKING:
    from openglider.glider.rib.rib import Rib


@dataclass
class Sharknose:
    position: float
    amount: float
    
    start: float
    end: float

    angle_front: float=1.
    angle_back: float=0.8


    rigidfoil_circle_radius: float = 0.05
    rigidfoil_circle_amount: float = 0.4

    def get_modified_airfoil(self, rib: Rib) -> openglider.airfoil.Profile2D:
        data = []

        ik_start = rib.profile_2d.get_ik(self.start)
        ik_position = round(rib.profile_2d.get_ik(self.position))
        ik_end = rib.profile_2d.get_ik(self.end)

        point_start = rib.profile_2d.curve.get(ik_start)
        point_position = rib.profile_2d.curve.get(ik_position)
        position = point_position[0]
        point_end = rib.profile_2d.curve.get(ik_end)

        point_position[1] = point_position[1] + (point_start[1]-point_position[1])*self.amount

        tangents = euklid.vector.PolyLine2D(rib.profile_2d.curve.get_tangents())
        def get_tangent(ik: float, from_point: euklid.vector.Vector2D, to_point: euklid.vector.Vector2D, amount: float) -> euklid.vector.Vector2D:
            #ik -= 0.5
            #ik = max(ik, 0)
            #ik = min(ik, len(tangents)-1)

            tangent = tangents.get(ik).normalized()

            scale = float("inf")
            if abs(tangent[1]) > 0:
                scale = abs((from_point[1]-to_point[1])/tangent[1])
            if abs(tangent[0]) > 0:
                scale = min(scale, abs((from_point[0]-to_point[0])/tangent[0]))

            return tangent * scale * amount

        curve_1 = euklid.spline.BSplineCurve([
            point_start,
            point_start + get_tangent(ik_start, point_start, point_position, self.angle_front),
            point_position
        ]).get_sequence(50)

        curve_2 = euklid.spline.BSplineCurve([
            point_position,
            point_end - get_tangent(ik_end, point_end, point_position, self.angle_back),
            point_end
        ]).get_sequence(50)

        interpolation_1 = euklid.vector.Interpolation(curve_1.nodes)
        interpolation_2 = euklid.vector.Interpolation(curve_2.nodes)
        

        for i, point in enumerate(rib.profile_2d.curve):
            x = point[0]
            y = point[1]
            
            if i > rib.profile_2d.noseindex:
                if x > self.start and x <= self.position:
                    y = interpolation_1.get_value(x)
                elif x > self.position and x < self.end:
                    y = interpolation_2.get_value(x)

            data.append(euklid.vector.Vector2D([x, y]))
        
        return openglider.airfoil.Profile2D(data)

    def update_rigidfoils(self, rib: "Rib") -> typing.List[RigidFoilBase]:
        result: typing.List[RigidFoilBase] = []

        nearest_position = round(rib.profile_2d.get_ik(self.position))
        position = Percentage(rib.profile_2d.curve.get(nearest_position)[0])

        for rigidfoil in rib.rigidfoils:
            if rigidfoil.start < position and rigidfoil.end > position:
                # split rigidfoil
                rigid_1 = RigidFoilCurved(
                    start=rigidfoil.start,
                    end=position,
                    distance=rigidfoil.distance
                )
                radius, amount =  rigidfoil.get_cap_radius(start=True)
                rigid_1.circle_radius_start = radius
                rigid_1.circle_amount_start = amount
                rigid_1.circle_radius_end = self.rigidfoil_circle_radius
                rigid_1.circle_amount_end = self.rigidfoil_circle_amount

                rigid_2 = RigidFoilCurved(
                    start=position,
                    end=rigidfoil.end,
                    distance=rigidfoil.distance
                )
                radius, amount =  rigidfoil.get_cap_radius(start=False)
                rigid_2.circle_radius_end = radius
                rigid_2.circle_amount_end = amount
                rigid_2.circle_radius_start = self.rigidfoil_circle_radius
                rigid_2.circle_amount_start = self.rigidfoil_circle_amount

                result += [rigid_1, rigid_2]
            else:
                result.append(rigidfoil)
        
        return result
