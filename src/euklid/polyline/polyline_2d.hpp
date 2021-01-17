#pragma once

#include <algorithm>
#include "euklid/polyline/polyline.hpp"
#include "euklid/vector/cut_2d.hpp"

class PolyLine2D : public PolyLine<Vector2D> {
    public:
        using PolyLine<Vector2D>::PolyLine;
        
        PolyLine2D resample(int num_points);
        PolyLine2D normvectors();
        PolyLine2D offset(double amount);

        std::vector<std::pair<double, double>> cut(Vector2D& p1, Vector2D& p2);
        PolyLine2D fix_errors();
};