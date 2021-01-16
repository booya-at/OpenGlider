#pragma once

#include "vector_2d.hpp"

struct CutResult {
    bool success;
    float ik_1;
    float ik_2;
};

CutResult cut(Vector2D l1_p1, Vector2D l1_p2, Vector2D l2_p1, Vector2D l2_p2) {
    
}