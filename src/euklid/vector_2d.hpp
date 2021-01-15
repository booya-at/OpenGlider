#pragma once

#include<vector>
#include <math.h>
#include <iostream>

class Vector2D {
    public:
        Vector2D(const Vector2D&);
        Vector2D(double, double);
        Vector2D();

        double x;
        double y;

        double get_item(int n) const;
        void set_item(int n, double value);

        double& operator[] (int n);
        double operator[] (int n) const;
        Vector2D operator -(const Vector2D& v2);
        Vector2D operator +(const Vector2D& v2);
        //Vector2D operator *(const Vector2D& v2);
        Vector2D operator *(const double&);

        double dot(Vector2D& v2);
        double distance(Vector2D& v2);
        double length();

        Vector2D copy();

};