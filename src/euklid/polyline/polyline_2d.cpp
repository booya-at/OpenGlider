#include "polyline_2d.hpp"
#include "common.cpp"


PolyLine2D PolyLine2D::resample(int num_points) {
    return resample_template<PolyLine2D, Vector2D>(this, num_points);
}


bool PolyLine2D::validate() {
    return true;
};