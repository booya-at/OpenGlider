#include "euklid/polyline/polyline.hpp"


class PolyLine2D : public PolyLine<Vector2D> {
    public:
        using PolyLine<Vector2D>::PolyLine;
        bool validate();
        
        PolyLine2D resample(int num_points);
};