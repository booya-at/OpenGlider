#pragma once

#include<vector>
#include <math.h>
#include <iostream>

class Vector3D {
    public:
        Vector3D(const Vector3D&);
        Vector3D(double, double, double);
        Vector3D();

        double x;
        double y;
        double z;

        double get_item(int n) const;
        void set_item(int n, double value);

        double& operator[] (int n);
        double operator[] (int n) const;
        Vector3D operator -(const Vector3D& v2);
        Vector3D operator +(const Vector3D& v2);
        //Vector3D operator *(const Vector3D& v2);
        Vector3D operator *(const double&);

        double dot(Vector3D& v2);
        double distance(Vector3D& v2);
        double length();

        Vector3D copy();

};