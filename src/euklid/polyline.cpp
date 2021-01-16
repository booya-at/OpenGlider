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
    if ((start - next_value) < 1e-5){
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

template<typename PolyLineClass, typename VectorClass>
PolyLineClass resample_template(PolyLineClass *self, int num_points) {
    float distance = self->get_length() / (num_points-1);
    float ik = 0;
    std::vector<std::shared_ptr<VectorClass>> nodes_new;

    nodes_new.push_back(self->get(0.));
    
    for (int i=0; i<num_points-2; i++) {
        ik = self->walk(ik, distance);
        nodes_new.push_back(self->get(ik));
    }

    nodes_new.push_back(std::make_shared<VectorClass>(*self->nodes.back()));

    return PolyLineClass(nodes_new);
}

PolyLine2D PolyLine2D::resample(int num_points) {
    return resample_template<PolyLine2D, Vector2D>(this, num_points);
}

PolyLine3D PolyLine3D::resample(int num_points) {
    return resample_template<PolyLine3D, Vector3D>(this, num_points);
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