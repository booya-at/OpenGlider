#include "vector.hpp"

template<unsigned int dimensions, typename T>
Vector<dimensions, T>::Vector(const T& in) {
    for(int i=0; i<dimensions; i++){
        this->set_item(i, in.get_item(i));
    }
}


template<unsigned int dimensions, typename T>
Vector<dimensions, T>::Vector(const Vector<dimensions, T>& in) {
    for(int i=0; i<dimensions; i++){
        this->set_item(i, in.get_item(i));
    }
}


template<unsigned int dimensions, typename T>
Vector<dimensions, T>::Vector() {
    for(int i=0; i<dimensions; i++){
        this->set_item(i, 0);
    }
}

template<unsigned int dimensions, typename T>
Vector<dimensions, T>::Vector(double value) {
    for(int i=0; i<dimensions; i++){
        this->set_item(i, value);
    }
}

/*
template<unsigned int dimensions, typename T>
double Vector<dimensions, T>::dot(const Vector<dimensions, T>& v2) {
    double result = 0;

    for (int i=0; i<dimensions; i++) {
        result += this->get_item(i) * v2.get_item(i);
    }

    return result;
}*/

template<unsigned int dimensions, typename T>
double Vector<dimensions, T>::dot(const T& v2) {
    double result = 0;

    for (int i=0; i<dimensions; i++) {
        result += this->get_item(i) * v2.get_item(i);
    }

    return result;
}


template<unsigned int dimensions, typename T>
double Vector<dimensions, T>::length(){
    return sqrt(this->dot(static_cast<T>(*this)));
}

template<unsigned int dimensions, typename T>
double Vector<dimensions, T>::get_item(int n) const {
    if (n < 0 || n >= dimensions) {
        throw "Invalid dimension";
    }

    return this->coordinates[n];
}


template<unsigned int dimensions, typename T>
void Vector<dimensions, T>::set_item(int n, double value) {
    if (n < 0 || n >= dimensions) {
        throw "Invalid dimension";
    }

    this->coordinates[n] = value;
}

template<unsigned int dimensions, typename T>
double& Vector<dimensions, T>::operator[](int n) {
    if (n < 0 || n >= dimensions) {
        throw "Invalid dimension";
    }

    return this->coordinates[n];
}


template<unsigned int dimensions, typename T>
double Vector<dimensions, T>::operator[](int n) const {
    return this->get_item(n);
}

template<unsigned int dimensions, typename T>
T Vector<dimensions, T>::operator+(const T& v2) const {
    T result;

    for (int i=0; i<dimensions; i++){
        result.set_item(i, this->get_item(i) + v2.get_item(i));
    }

    return result;
}

template<unsigned int dimensions, typename T>
T Vector<dimensions, T>::operator-(const T& v2) const {
    T result;

    for(int i=0; i<dimensions; i++) {
        result.set_item(i, this->get_item(i) - v2.get_item(i));
    }

    return result;
}

template<unsigned int dimensions, typename T>
T Vector<dimensions, T>::operator*(const T& v2) const {
    T result;

    for (int i=0; i<dimensions; i++){
        result.set_item(i, this->get_item(i) * v2.get_item(i));
    }

    return result;
}


template<unsigned int dimensions, typename T>
T Vector<dimensions, T>::operator* (const double& factor) const {
    T result;

    for (int i=0; i<dimensions; i++) {
        result.set_item(i, this->get_item(i)*factor);
    }

    return result;
}

template<unsigned int dimensions, typename T>
double Vector<dimensions, T>::distance(const T& v2) {
    return ((*this) - v2).length();
}

template<unsigned int dimensions, typename T>
T Vector<dimensions, T>::copy() {
    return T(*this);
}

template<unsigned int dimensions, typename T>
void Vector<dimensions, T>::normalize() {
    double len = this->length();

    for (int i=0; i<dimensions; i++) {
        this->set_item(i, this->get_item(i)/len);
    }
}

Vector2D::Vector2D(double x, double y) {
    this->set_item(0, x);
    this->set_item(1, y);
}

Vector3D::Vector3D(double x, double y, double z) {
    this->set_item(0, x);
    this->set_item(1, y);
    this->set_item(2, z);
}

Vector3D::Vector3D() {
    this->set_item(0,0);
    this->set_item(1,0);
    this->set_item(2,0);
}
Vector2D::Vector2D() {
    this->set_item(0,0);
    this->set_item(1,0);
}


Vector2D::Vector2D(const Vector<2, Vector2D>& in) {
    for(int i=0; i<Vector2D::dimension; i++){
        this->set_item(i, in.get_item(i));
    }
}
Vector3D::Vector3D(const Vector<3, Vector3D>& in) {
    for(int i=0; i<Vector3D::dimension; i++){
        this->set_item(i, in.get_item(i));
    }
}




template class Vector<3, Vector3D>;
template class Vector<2, Vector2D>;