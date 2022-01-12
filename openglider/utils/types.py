from typing import Union
import euklid

AsymmetricCurveType = Union[
    euklid.spline.BSplineCurve,
    euklid.spline.BezierCurve,
    euklid.spline.CubicBSplineCurve,
    euklid.spline.QuadBSplineCurve
    ]

SymmetricCurveType = Union[
    euklid.spline.SymmetricBSplineCurve,
    euklid.spline.SymmetricBezierCurve,
    euklid.spline.SymmetricCubicBSplineCurve,
    euklid.spline.SymmetricQuadBSplineCurve
    ]
    
CurveType = Union[AsymmetricCurveType, SymmetricCurveType]