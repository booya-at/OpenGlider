#include "vector_3d.hpp"

Vector3D::Vector3D(const Vector3D& in): 
    x(in.x), y(in.y), z(in.z) {}


Vector3D::Vector3D(double x, double y, double z) {
    this->x = x;
    this->y = y;
    this->z = z;
}

Vector3D::Vector3D(): x(0), y(0), z(0) {}


double Vector3D::dot(Vector3D& v2) {
    double result = this->x * v2.x;

    result += this->y * v2.y;
    result += this->z * v2.z;

    return result;
}

double Vector3D::length(){
    return sqrt(this->dot(*this));
}

double Vector3D::get_item(int n) const {
    switch(n){
        case 0:
            return this->x;
        case 1:
            return this->y;
        case 2:
            return this->z;
        default:
            throw "Can only access 0, 1 or 2";
    }
}

void Vector3D::set_item(int n, double value) {
    switch(n){
        case 0:
            this->x = value;
            break;
        case 1:
            this->y = value;
            break;
        case 2:
            this->z = value;
            break;
        default:
            throw "Can only access 0, 1 or 2";
    }
}

double& Vector3D::operator[](int n) {
    switch(n){
        case 0:
            return this->x;
        case 1:
            return this->y;
        case 2:
            return this->z;
        default:
            throw "Can only access 0, 1 or 2";
    }
}
double Vector3D::operator[](int n) const {
    return (*this)[n];
}

Vector3D Vector3D::operator+(const Vector3D& v2) const {
    Vector3D result;
    
    for (int i=0; i<3; i++){
        result.set_item(i, this->get_item(i) + v2.get_item(i));
     }

    return result;
}

Vector3D Vector3D::operator-(const Vector3D& v2) const {
    Vector3D result;

    for(int i=0; i<3; i++) {
        result.set_item(i, this->get_item(i) - v2.get_item(i));
    }

    return result;
}

/*Vector3D Vector3D::operator*(const Vector3D& v2) {
    Vector3D result;
    // TODO: cross product

    return result;
}*/

Vector3D Vector3D::operator*(const double& factor) const {
    Vector3D result;

    result.x = this->x * factor;
    result.y = this->y * factor;
    result.z = this->z * factor;

    return result;
}

double Vector3D::distance(Vector3D& v2) {
    return ((*this) - v2).length();
}

Vector3D Vector3D::copy() {
    return Vector3D(this->x, this->y, this->z);
}