#include "vector.hpp"

template<unsigned int dimensions, typename T>
Vector<dimensions, T>::Vector(const T& in) {
    for(unsigned int i=0; i<dimensions; i++){
        this->set_item(i, in.get_item(i));
    }
}


template<unsigned int dimensions, typename T>
Vector<dimensions, T>::Vector() {
    for(unsigned int i=0; i<dimensions; i++){
        this->set_item(i, 0);
    }
}

template<unsigned int dimensions, typename T>
Vector<dimensions, T>::Vector(double value) {
    for(unsigned int i=0; i<dimensions; i++){
        this->set_item(i, value);
    }
}

/*
template<unsigned int dimensions, typename T>
double Vector<dimensions, T>::dot(const Vector<dimensions, T>& v2) {
    double result = 0;

    for (unsigned int i=0; i<dimensions; i++) {
        result += this->get_item(i) * v2.get_item(i);
    }

    return result;
}*/

template<unsigned int dimensions, typename T>
double Vector<dimensions, T>::dot(const T& v2) {
    double result = 0;

    for (unsigned int i=0; i<dimensions; i++) {
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
    if (n < 0 || n >= (int)dimensions) {
        throw "Invalid dimension";
    }

    return this->coordinates[n];
}


template<unsigned int dimensions, typename T>
void Vector<dimensions, T>::set_item(int n, double value) {
    if (n < 0 || n >= (int)dimensions) {
        throw "Invalid dimension";
    }

    this->coordinates[n] = value;
}

template<unsigned int dimensions, typename T>
double& Vector<dimensions, T>::operator[](int n) {
    if (n < 0 || n >= (int)dimensions) {
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

    for (unsigned int i=0; i<dimensions; i++){
        result.set_item(i, this->get_item(i) + v2.get_item(i));
    }

    return result;
}

template<unsigned int dimensions, typename T>
T Vector<dimensions, T>::operator-(const T& v2) const {
    T result;

    for(unsigned int i=0; i<dimensions; i++) {
        result.set_item(i, this->get_item(i) - v2.get_item(i));
    }

    return result;
}

template<unsigned int dimensions, typename T>
T Vector<dimensions, T>::operator*(const T& v2) const {
    T result;

    for (unsigned int i=0; i<dimensions; i++){
        result.set_item(i, this->get_item(i) * v2.get_item(i));
    }

    return result;
}


template<unsigned int dimensions, typename T>
T Vector<dimensions, T>::operator* (const double& factor) const {
    T result;

    for (unsigned int i=0; i<dimensions; i++) {
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

    for (unsigned int i=0; i<dimensions; i++) {
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


double Vector2D::cross(const Vector2D& v2) const {
    return (*this)[0] * v2[1] - v2[0] * (*this)[1];
}


Vector2D::Vector2D() {
    this->set_item(0,0);
    this->set_item(1,0);
}


Vector2D::Vector2D(const Vector<2, Vector2D>& in) {
    for(unsigned int i=0; i<Vector2D::dimension; i++){
        this->set_item(i, in.get_item(i));
    }
}
Vector3D::Vector3D(const Vector<3, Vector3D>& in) {
    for(unsigned int i=0; i<Vector3D::dimension; i++){
        this->set_item(i, in.get_item(i));
    }
}




template class Vector<3, Vector3D>;
template class Vector<2, Vector2D>;


CutResult cut_2d(const Vector2D& l1_p1, const Vector2D& l1_p2, const Vector2D& l2_p1, const Vector2D& l2_p2) {
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