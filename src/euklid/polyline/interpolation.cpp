#include "euklid/polyline/interpolation.hpp"

double Interpolation::get_value(double x) const {
    Vector2D p1(x, 0);
    Vector2D p2(x, 1);
    auto cuts = this->cut(p1, p2);

    if (cuts.size() <= 0) {
        throw std::runtime_error("No match!");
    }

    return this->get(cuts[0].first)->get_item(1);
}


Interpolation Interpolation::operator*(double scale) const {
    std::vector<std::shared_ptr<Vector2D>> nodes_new;

    for (auto node: this->nodes) {
        nodes_new.push_back(std::make_shared<Vector2D>(node->get_item(0), node->get_item(1)*scale));
    }

    return Interpolation(nodes_new);
}

Interpolation Interpolation::operator+(const Interpolation& other) const {
    std::vector<std::shared_ptr<Vector2D>> nodes_new;

    for (auto node: this->nodes) {
        double x = node->get_item(0);
        nodes_new.push_back(std::make_shared<Vector2D>(
            x,
            node->get_item(1) + other.get_value(x)
            ));
    }

    return Interpolation(nodes_new);
}

Interpolation Interpolation::copy() const {
    return *(this) * 1.;

}