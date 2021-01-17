#pragma once

#include "vector.hpp"

struct CutResult {
    bool success;
    float ik_1;
    float ik_2;
    Vector2D point;
};

CutResult static cut_2d(const Vector2D& l1_p1, const Vector2D& l1_p2, const Vector2D& l2_p1, const Vector2D& l2_p2) {
    CutResult result;
    // Line AB represented as a1x + b1y = c1
    double a1 = l1_p2[1] - l1_p1[1];
    double b1 = l1_p1[0] - l1_p2[0];
    double c1 = a1*l1_p1[0] + b1*l1_p1[1];
  
    // Line CD represented as a2x + b2y = c2 
    double a2 = l2_p2[1] - l2_p1[1];
    double b2 = l2_p1[0] - l2_p2[0];
    double c2 = a2*l2_p1[0] + b2*l2_p1[1];
  
    double determinant = a1*b2 - a2*b1; 
  
    if (determinant == 0) { 
        // Parallel lines!
        result.success = false;
    } else { 
        double x = (b2*c1 - b1*c2)/determinant; 
        double y = (a1*c2 - a2*c1)/determinant; 

        result.success = true;
        result.point.set_item(0, x);
        result.point.set_item(1, y);

        auto diff1 = l1_p2 - l1_p1;
        result.ik_1 = (result.point - l1_p1).dot(diff1) / diff1.dot(diff1);

        auto diff2 = (l2_p2 - l2_p1);
        result.ik_2 = (result.point - l2_p1).dot(diff2) / diff2.dot(diff2);
    }

    return result;
}