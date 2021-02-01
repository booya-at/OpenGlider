#pragma once

#include <array>
#include<cmath>

#include "euklid/vector/vector.hpp"
#include "euklid/polyline/polyline.hpp"
#include "euklid/polyline/polyline_2d.hpp"



class Transformation {
    using matrix_type = std::array<std::array<double, 4>, 4>;

    public:
        Transformation();
        Transformation(matrix_type);

        Transformation static rotation(double, Vector3D);
        Transformation static translation(const Vector3D&);
        Transformation static translation(const Vector2D&);
        Transformation static reflection(const Vector3D&);
        Transformation static scale(double);
        
        Transformation chain(const Transformation&) const;
        Transformation operator*(const Transformation&) const;
        Transformation copy() const;
        
        Vector3D apply(const Vector3D&) const;
        Vector3D apply(const Vector2D&) const;

        PolyLine3D apply(const PolyLine2D&) const;
        PolyLine3D apply(const PolyLine3D&) const;

        matrix_type matrix;

};