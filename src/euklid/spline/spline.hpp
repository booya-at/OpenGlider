#pragma once

#include <functional>
#include <Eigen/Dense>

#include "euklid/vector/vector.hpp"
#include "euklid/polyline/polyline_2d.hpp"
#include "euklid/spline/basis.hpp"


template<typename Base, typename T>
class SplineCurve {
    public:
        SplineCurve(PolyLine2D);

        Vector2D get(double);
        PolyLine2D get_sequence(size_t);

        PolyLine2D controlpoints;
        T copy() const;

        static T fit(const PolyLine2D&, size_t);
    
    private:
        Base& get_base();
        Base base;
};

class BezierCurve : public SplineCurve<BezierBase, BezierCurve> {
        using SplineCurve<BezierBase, BezierCurve>::SplineCurve;
};
class BSplineCurve : public SplineCurve<BSplineBase<2>, BSplineCurve> {
        using SplineCurve<BSplineBase<2>, BSplineCurve>::SplineCurve;
};

template<typename SplineClass, typename T>
class SymmetricSpline {
    public:
        SymmetricSpline(PolyLine2D);

        Vector2D get(double);
        PolyLine2D get_sequence(size_t);

        PolyLine2D controlpoints;
        T copy() const;

        static T fit(const PolyLine2D&, size_t);
    
    private:
        void apply();
        SplineClass spline_curve;
};

class SymmetricBSplineCurve : public SymmetricSpline<BSplineCurve, SymmetricBSplineCurve> {
        using SymmetricSpline<BSplineCurve, SymmetricBSplineCurve>::SymmetricSpline;
};