#pragma once

#include<vector>
#include <math.h>
#include <iostream>

template<unsigned int dimensions, typename T>
class Vector {
    public:
        /*
        */
        Vector(const T&);
        Vector(const Vector<dimensions, T>&);
        Vector();
        
        static const int dimension = dimensions;

        double get_item(int n) const;
        void set_item(int n, double value);

        double& operator[] (int n);
        double operator[] (int n) const;
        T operator -(const T& v2) const;
        T operator +(const T& v2) const;
        //Vector3D operator *(const Vector3D& v2);
        T operator *(const double&) const;

        double dot(const T& v2);
        //double dot(const T& v2);
        double distance(const T& v2);
        double length();

        void normalize();

        T copy();
    
    //private:
        double coordinates[dimensions];
};


class Vector2D: public Vector<2, Vector2D> {
    public:
        using Vector<2, Vector2D>::Vector;
        Vector2D();
        Vector2D(const Vector<2, Vector2D>&);
        Vector2D(float x, float y);
};

class Vector3D : public Vector<3, Vector3D> {
    public:
        using Vector<3, Vector3D>::Vector;
        Vector3D();
        Vector3D(const Vector<3, Vector3D>&);
        Vector3D(float x, float y, float z);
};