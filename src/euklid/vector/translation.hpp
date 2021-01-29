#pragma once

#include <array>
#include<cmath>

#include "euklid/vector/vector.hpp"




class Translation {
    using matrix_type = std::array<std::array<double, 4>, 4>;

    public:
        Translation();
        Translation(matrix_type);

        Translation static rotation(double, Vector3D);
        Translation static translation(const Vector3D&);
        Translation static translation(const Vector2D&);
        Translation static reflection(const Vector3D&);
        Translation static scale(double);
        
        Translation chain(const Translation&) const;

        Vector3D apply(const Vector3D&) const;
        Vector2D apply(const Vector2D&) const;

        matrix_type matrix;

};