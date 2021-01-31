#pragma once

#include <functional>

#include "euklid/vector/vector.hpp"
#include "euklid/polyline/polyline_2d.hpp"


class BezierBase {
    public:
        BezierBase(size_t size);

        size_t dimension() const;
        double get(size_t index, double value) const;

    private:
        std::vector<std::function<double(double)>> bases;
};


template<size_t degree>
class BSplineBase {
    public:
        BSplineBase(size_t size);

        size_t dimension() const;
        double get(size_t index, double value) const;
    
    private:
        std::function<double(double)> get_basis(size_t, size_t);

        std::vector<double> knots;
        std::vector<std::function<double(double)>> bases;
};

