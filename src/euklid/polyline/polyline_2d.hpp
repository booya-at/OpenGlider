#pragma once

#include <algorithm>
#include "euklid/vector/vector.hpp"
#include "euklid/polyline/polyline.hpp"
#include "euklid/vector/rotation_2d.hpp"

class PolyLine2D : public PolyLine<Vector2D, PolyLine2D> {
    public:
        using PolyLine<Vector2D, PolyLine2D>::PolyLine;
        
        //PolyLine2D resample(int num_points);
        PolyLine2D normvectors();
        PolyLine2D offset(double amount);

        std::vector<std::pair<double, double>> cut(Vector2D& p1, Vector2D& p2) const;
        std::pair<double, double> cut(Vector2D& p1, Vector2D& p2, double nearest_ik) const;
        PolyLine2D fix_errors();

        PolyLine2D mirror(Vector2D& p1, Vector2D& p2) const;
        PolyLine2D rotate(double, Vector2D&);

        PolyLine3D to_3d() const;
};