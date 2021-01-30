#include "euklid/spline/spline.hpp"


template<typename Base, typename T>
SplineCurve<Base, T>::SplineCurve(PolyLine2D controlpoints) : 
    controlpoints(controlpoints),
    base(controlpoints.nodes.size())  {}

template<typename Base, typename T>
Base& SplineCurve<Base, T>::get_base() {
    if (this->base.dimension() != this->controlpoints.nodes.size()){
        this->base = Base(this->controlpoints.nodes.size());
    }

    return this->base;
}

template<typename Base, typename T>
Vector2D SplineCurve<Base, T>::get(double ik) {
    auto base = this->get_base();
    Vector2D result;
    
    for (unsigned int i=0; i<this->controlpoints.nodes.size(); i++) {
        result = result + *this->controlpoints.nodes[i] * base.get(i, ik);
    }

    return result;
}

template<typename Base, typename T>
PolyLine2D SplineCurve<Base, T>::get_sequence(unsigned int segments) {
    std::vector<std::shared_ptr<Vector2D>> nodes_new;

    for (unsigned int i=0; i<=segments; i++) {
        nodes_new.push_back(std::make_shared<Vector2D>(this->get(static_cast<double>(i)/segments)));
    }

    return PolyLine2D(nodes_new);
}


template<typename Base, typename T>
T SplineCurve<Base, T>::fit(const PolyLine2D& line, int numpoints) {
    using NodeList = std::vector<std::shared_ptr<Vector2D>>;
    auto base = Base(numpoints);
    unsigned int rows = line.nodes.size();
    unsigned int columns = base.dimension();
    NodeList nodes_new;

    nodes_new.push_back(std::make_shared<Vector2D>(*line.nodes[0]));

    // Influence Matrices
    Eigen::MatrixXd A1(rows, columns-2); // nodes influence vector
    Eigen::MatrixXd A2(rows, 2);  // start/end point

    for (uint row=0; row<line.nodes.size(); row++) {
        // p_0 [A1...] p_columns
        for (uint column=1; column<columns-1; column++) {
            auto coeff = base.get(column, (double)row/(line.nodes.size()-1));
            A1(row, column-1) = coeff;
        }

        A2(row, 0) = base.get(0, (double)row/(rows-1));
        A2(row, 1) = base.get(columns-1, (double)row/(rows-1));
    }

    // result
    Eigen::MatrixXd p1(2, columns);
    Eigen::MatrixXd p2(2, 2);

    for (uint dim=0; dim<2; dim++) {
        for (uint column=0; column<columns; column++){
            p1(dim, column) = line.nodes[column]->get_item(dim);
        }

        p2(dim, 0) = line.nodes[0]->get_item(dim);
        p2(dim, 1) = line.nodes.back()->get_item(dim);
    }

    auto A1_transposed = A1.transpose();
    auto A1_tdot = A1_transposed*A1;
    auto A1_inverse = A1_tdot.inverse();
    
    Eigen::MatrixXd solution(2, columns-2);
    for (int dim=0; dim<2; dim++) {
        auto p1_dim = p1.row(dim).transpose();
        auto rhs_1 = A1_transposed * p1_dim;
        auto p2_dim = p2.row(dim).transpose();
        auto rhs_2 = ((A1_transposed * A2) * p2_dim);

        solution.row(dim) = A1_inverse * (rhs_1-rhs_2);
    }

    for (uint i=0; i<columns-2; i++) {
        auto vector = std::make_shared<Vector2D>();
        for (uint dim=0; dim<2; dim++) {
            vector->set_item(dim, solution(dim, i));
        }
        nodes_new.push_back(vector);
    }

    nodes_new.push_back(std::make_shared<Vector2D>(*line.nodes.back()));

    return T(PolyLine2D(nodes_new));
}

template class SplineCurve<BezierBase, BezierCurve>;
template class SplineCurve<BSplineBase<2>, BSplineCurve>;