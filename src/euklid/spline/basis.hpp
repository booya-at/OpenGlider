#pragma once

#include <functional>

#include "euklid/vector/vector.hpp"
#include "euklid/polyline/polyline_2d.hpp"


class BezierBase {
    public:
        BezierBase(unsigned int size);

        unsigned int dimension() const;
        double get(unsigned int index, double value) const;

    private:
        std::vector<std::function<double(double)>> bases;
};


template<unsigned int degree>
class BSplineBase {
    public:
        BSplineBase(unsigned int size);

        unsigned int dimension() const;
        double get(unsigned int index, double value) const;
    
    private:
        std::function<double(double)> get_basis(uint, uint);

        std::vector<double> knots;
        std::vector<std::function<double(double)>> bases;
};

