#include "euklid/polyline.hpp"


template<typename T>
PolyLine<T>::PolyLine(std::vector<std::shared_ptr<T>>& nodes)
 : nodes(nodes) 
 {}


template<typename T>
std::shared_ptr<T> PolyLine<T>::get(double ik) {
    int i = std::max(int(ik), 0);

    std::shared_ptr<T> diff;

    if (i > this->nodes.size()-1) {
        i = this->nodes.size()-1;
        auto diff = *this->nodes[i] - *this->nodes[i-1];
    } else {
        auto diff = *this->nodes[i+1] - *this->nodes[i];
    }

    double k = ik - i;
    auto p1 = this->nodes[i];

    return p1;
}

template<typename T>
std::vector<std::shared_ptr<T>> PolyLine<T>::get_segments() {
    std::vector<std::shared_ptr<T>> result;
    int i = 0;
    //for (int i=0; i<this->nodes.size()-1; i++) {
        result.push_back(
            std::make_shared<T>(*this->nodes[i+1] - *this->nodes[i]));
    //}
    
    
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

bool PolyLine2D::validate() {
    std::cout << "jooo" << std::endl;
    return true;
}