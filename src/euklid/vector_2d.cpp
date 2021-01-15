#include "vector_2d.hpp"


Vector2D::Vector2D(double x, double y) : x(x), y(y) {}

Vector2D::Vector2D(): x(0), y(0) {}


double Vector2D::dot(Vector2D& v2) {
    double result = this->x * v2.x;

    result += this->y * v2.y;

    return result;
}

double Vector2D::length(){
    return sqrt(this->dot(*this));
}

double Vector2D::get_item(int n) const {
    switch(n){
        case 0:
            return this->x;
        case 1:
            return this->y;
        default:
            throw "Can only access 0, 1 or 2";
    }
}

void Vector2D::set_item(int n, double value) {
    switch(n){
        case 0:
            this->x = value;
            break;
        case 1:
            this->y = value;
            break;
        default:
            throw "Can only access 0, 1 or 2";
    }
}

double& Vector2D::operator[](int n) {
    switch(n){
        case 0:
            return this->x;
        case 1:
            return this->y;
        default:
            throw "Can only access 0, 1 or 2";
    }
}
double Vector2D::operator[](int n) const {
    return (*this)[n];
}

Vector2D Vector2D::operator+(const Vector2D& v2) {
    Vector2D result;
    float res2=0;

    std::cout << "substracting" << std::endl;

    for (int i=0; i<2; i++){
        //result[i] = (*this)[i] + v2[i];
        result.set_item(i, this->get_item(i) + v2.get_item(i));
        //result.set_item(i, i);
    }

    std::cout << "substracting2" << std::endl;

    return result;
}

Vector2D Vector2D::operator-(const Vector2D& v2) {
    Vector2D result;

    for(int i=0; i<2; i++) {
        result.set_item(i, this->get_item(i) - v2.get_item(i));
    }

    return result;
}

/*Vector2D Vector2D::operator*(const Vector2D& v2) {
    Vector2D result;
    // TODO: cross product

    return result;
}*/

Vector2D Vector2D::operator*(const double& factor) {
    Vector2D result;

    result.x = this->x * factor;
    result.y = this->y * factor;

    return result;
}

double Vector2D::distance(Vector2D& v2) {
    return ((*this) - v2).length();
}

Vector2D Vector2D::copy() {
    return Vector2D(this->x, this->y);
}