#include "euklid/polyline/polyline.hpp"
#include "common.cpp"

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
std::vector<double> PolyLine<T>::get_segment_lengthes() {
    std::vector<double> result;

    for (auto segment: this->get_segments()) {
        result.push_back(segment->length());
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
double PolyLine<T>::walk(double start, double amount) {

    int direction = 1;
    if (amount < 0) {
        direction = -1;
    }

    int next_value = int(start);
    if (amount > 0) {
        next_value += 1;
    }
    
    if (std::abs(start - next_value) < 1e-5){
        next_value += direction;
    }

    amount = std::abs(amount);

    float current_segment_length = (*this->get(next_value) - *this->get(start)).length();
    amount -= current_segment_length;
    
    while (amount > 0) {
        if (next_value > this->nodes.size() && direction > 0) {
            break;
        }
        if (next_value < 0 and direction < 0) {
            break;
        }

        start = next_value;
        next_value += direction;
        current_segment_length = (*this->get(next_value) - *this->get(start)).length();

        amount -= current_segment_length;
    }

    return next_value + direction * amount * std::abs(next_value - start) / current_segment_length;
}



template<typename T>
int PolyLine<T>::__len__() {
    return this->nodes.size();
}

PolyLine3D PolyLine3D::resample(int num_points) {
    return resample_template<PolyLine3D, Vector3D>(this, num_points);
}


template class PolyLine<Vector3D>;
template class PolyLine<Vector2D>;