#include "euklid/polyline/polyline_2d.hpp"


class Interpolation : public PolyLine2D {
    public:
        //using PolyLine<Vector2D, PolyLine2D>::PolyLine;
        using PolyLine2D::PolyLine2D;
        double get_value(double) const;

        Interpolation operator*(double) const;
        Interpolation operator+(const Interpolation&) const;

        Interpolation copy() const;
};