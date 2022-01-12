from typing import Union
import euklid

AsymmetricCurveType = Union[
    euklid.spline.BSplineCurve,
    euklid.spline.BezierCurve,
    euklid.spline.CubicBSplineCurve
    ]

SymmetricCurveType = Union[
    euklid.spline.SymmetricBSplineCurve,
    euklid.spline.SymmetricBezierCurve,
    euklid.spline.SymmetricCubicBSplineCurve
    ]
    
CurveType = Union[AsymmetricCurveType, SymmetricCurveType]