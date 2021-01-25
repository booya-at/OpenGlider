#include "euklid/polyline/polyline.hpp"

template<typename VectorClass, typename T>
PolyLine<VectorClass, T>::PolyLine() : nodes() {}

template<typename VectorClass, typename T>
PolyLine<VectorClass, T>::PolyLine(std::vector<std::shared_ptr<VectorClass>>& nodes)
 : nodes(nodes) 
 {}


template<typename VectorClass, typename T>
std::shared_ptr<VectorClass> PolyLine<VectorClass, T>::get(double ik) {
    unsigned int i = std::max(int(ik), 0);
    VectorClass diff;

    if (i >= this->nodes.size()-1) {
        i = this->nodes.size()-1;
        diff = *this->nodes[i] - *this->nodes[i-1];
    } else {
        diff = *this->nodes[i+1] - *this->nodes[i];
    }

    double k = ik - i;
    auto p1 = this->nodes[i];

    return std::make_shared<VectorClass>(*p1 + diff*k);
}

template<typename VectorClass, typename T>
T PolyLine<VectorClass, T>::get(double ik_start, double ik_end) {
    std::vector<std::shared_ptr<VectorClass>> nodes_new;
    int direction = 1;
    bool forward = true;

    if (ik_end < ik_start) {
        direction = -1;
        forward = false;
    }

    // add first point
    nodes_new.push_back(this->get(ik_start));

    int ik = int(ik_start);

    ik = std::min(std::max((int)0, ik), (int)this->nodes.size()-2);

    if (forward) {
        ik += 1;
    }

    // todo: maybe check the length diff?
    if ((unsigned double)std::abs(ik_start-ik) < 1e-8) {
        ik += direction;
    }

    while (direction * (ik_end - ik) > 1e-8 && 0 < ik && ik < (int)this->nodes.size()-1) {
        nodes_new.push_back(std::make_shared<VectorClass>(*this->nodes[ik]));
        ik += direction;
    }

    nodes_new.push_back(this->get(ik_end));

    return T(nodes_new);
}

template<typename VectorClass, typename T>
std::vector<std::shared_ptr<VectorClass>> PolyLine<VectorClass, T>::get_segments() {
    std::vector<std::shared_ptr<VectorClass>> result;
    
    if (this->nodes.size() < 2) {
        return result;
    }
    for (unsigned int i=0; i<this->nodes.size()-1; i++) {
        result.push_back(
            std::make_shared<VectorClass>(*this->nodes[i+1] - *this->nodes[i]));
    }
    
    
    return result;
}

template<typename VectorClass, typename T>
std::vector<double> PolyLine<VectorClass, T>::get_segment_lengthes() {
    std::vector<double> result;

    for (auto segment: this->get_segments()) {
        result.push_back(segment->length());
    }

    return result;
}

template<typename VectorClass, typename T>
double PolyLine<VectorClass, T>::get_length() {
    auto segments = this->get_segments();
    double length = 0;
    for (auto segment: segments) {
        length += segment->length();
    }

    return length;
}

template<typename VectorClass, typename T>
double PolyLine<VectorClass, T>::walk(double start, double amount) {
    if (amount < 1e-5) {
        return start;
    }

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

    double current_segment_length = (*this->get(next_value) - *this->get(start)).length();
    amount -= current_segment_length;
    
    while (amount > 0) {
        if (next_value > (int)this->nodes.size() && direction > 0) {
            break;
        }
        if (next_value < 0 && direction < 0) {
            break;
        }

        start = next_value;
        next_value += direction;
        current_segment_length = (*this->get(next_value) - *this->get(start)).length();

        amount -= current_segment_length;
    }

    return next_value + direction * amount * std::abs(next_value - start) / current_segment_length;
}


template<typename VectorClass, typename T>
T PolyLine<VectorClass, T>::resample(const int num_points) {
    float distance = this->get_length() / (num_points-1);
    float ik = 0;
    std::vector<std::shared_ptr<VectorClass>> nodes_new;

    nodes_new.push_back(this->get(0.));
    
    for (int i=0; i<num_points-2; i++) {
        ik = this->walk(ik, distance);
        nodes_new.push_back(this->get(ik));
    }

    nodes_new.push_back(std::make_shared<VectorClass>(*this->nodes.back()));

    return T(nodes_new);
}

template<typename VectorClass, typename T>
T PolyLine<VectorClass, T>::copy() {
    std::vector<std::shared_ptr<VectorClass>> nodes_new;

    for (auto node: this->nodes) {
        nodes_new.push_back(std::make_shared<VectorClass>(*node));
    }

    return T(nodes_new);
}


template<typename VectorClass, typename T>
T PolyLine<VectorClass, T>::scale(const VectorClass& scale) {
    std::vector<std::shared_ptr<VectorClass>> nodes_new;

    for (auto node: this->nodes) {
        nodes_new.push_back(std::make_shared<VectorClass>(*node * scale));
    }

    return T(nodes_new);
}


template<typename VectorClass, typename T>
T PolyLine<VectorClass, T>::scale(const double scale) {
    auto scale_vector = VectorClass();
    for (int i=0; i<VectorClass::dimension; i++) {
        scale_vector.set_item(i, scale);
    }

    return this->scale(scale_vector);
}


template<typename VectorClass, typename T>
T PolyLine<VectorClass, T>::mix(T& other, const double amount) {
    if (other.nodes.size() != this->nodes.size()){
        throw "PolyLine sizes don't match!";
    }

    T line_1 = this->scale(1-amount);
    T line_2 = other.scale(amount);

    std::vector<std::shared_ptr<VectorClass>> nodes_new;

    for (unsigned int i=0; i<this->nodes.size(); i++) {
        auto node = *line_1.nodes[i] + *line_2.nodes[i];
        nodes_new.push_back(std::make_shared<VectorClass>(node));
    }

    return T(nodes_new);
}


template<typename VectorClass, typename T>
T PolyLine<VectorClass, T>::operator+ (const T& line2) const {
    std::vector<std::shared_ptr<VectorClass>> new_nodes;

    for (auto node: this->nodes) {
        new_nodes.push_back(std::make_shared<VectorClass>(*node));
    }

    for (auto node: line2.nodes) {
        new_nodes.push_back(std::make_shared<VectorClass>(*node));
    }

    return T(new_nodes);
}

template<typename VectorClass, typename T>
T PolyLine<VectorClass, T>::move (const VectorClass& offset) const {
    std::vector<std::shared_ptr<VectorClass>> new_nodes;

    for (auto node: this->nodes) {
        new_nodes.push_back(std::make_shared<VectorClass>(*node + offset));
    }

    return T(new_nodes);
}


template<typename VectorClass, typename T>
T PolyLine<VectorClass, T>::reverse() {
    return this->get(this->nodes.size()-1, 0);
}


template<typename VectorClass, typename T>
int PolyLine<VectorClass, T>::__len__() {
    return this->nodes.size();
}


template class PolyLine<Vector3D, PolyLine3D>;