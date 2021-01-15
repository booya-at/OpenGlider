#include "euklid/polyline.hpp"

template<typename T>
PolyLine<T>::PolyLine() : nodes() {}

template<typename T>
PolyLine<T>::PolyLine(std::vector<std::shared_ptr<T>>& nodes)
 : nodes(nodes) 
 {}


template<typename T>
std::shared_ptr<T> PolyLine<T>::get(double ik) {
    int i = std::max(int(ik), 0);
    T diff;

    if (i >= this->nodes.size()-1) {
        i = this->nodes.size()-1;
        diff = *this->nodes[i] - *this->nodes[i-1];
    } else {
        diff = *this->nodes[i+1] - *this->nodes[i];
    }

    double k = ik - i;
    auto p1 = this->nodes[i];

    return std::make_shared<T>(*p1 + diff*k);
}

template<typename T>
std::vector<std::shared_ptr<T>> PolyLine<T>::get_segments() {
    std::vector<std::shared_ptr<T>> result;
    
    if (this->nodes.size() < 2) {
        return result;
    }
    for (int i=0; i<this->nodes.size()-1; i++) {
        result.push_back(
            std::make_shared<T>(*this->nodes[i+1] - *this->nodes[i]));
    }
    
    
    return result;
}

template<typename T>
float PolyLine<T>::get_length() {
    auto segments = this->get_segments();
    double length = 0;
    for (auto segment: segments) {
        length += segment->length();
    }

    return length;
}

template<typename T>
int PolyLine<T>::__len__() {
    return this->nodes.size();
}

template class PolyLine<Vector3D>;
template class PolyLine<Vector2D>;

bool PolyLine2D::validate() {
    std::cout << "jooo" << std::endl;
    return true;
};