#include "euklid/spline/spline.hpp"


template<typename Base, typename T>
SplineCurve<Base, T>::SplineCurve(PolyLine2D controlpoints) : 
    controlpoints(controlpoints),
    base(controlpoints.nodes.size())  {}


template<typename Base, typename T>
T SplineCurve<Base, T>::copy() const {
    return T(this->controlpoints);
}

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
    
    for (size_t i=0; i<this->controlpoints.nodes.size(); i++) {
        result = result + *this->controlpoints.nodes[i] * base.get(i, ik);
    }

    return result;
}

template<typename Base, typename T>
PolyLine2D SplineCurve<Base, T>::get_sequence(size_t segments) {
    std::vector<std::shared_ptr<Vector2D>> nodes_new;

    for (size_t i=0; i<=segments; i++) {
        nodes_new.push_back(std::make_shared<Vector2D>(this->get(static_cast<double>(i)/segments)));
    }

    return PolyLine2D(nodes_new);
}


template<typename Base, typename T>
T SplineCurve<Base, T>::fit(const PolyLine2D& line, size_t numpoints) {
    using NodeList = std::vector<std::shared_ptr<Vector2D>>;


    if (numpoints > line.nodes.size()) {
        throw std::runtime_error("numpoints > line_points");
    }

    auto base = Base(numpoints);
    size_t rows = line.nodes.size();
    size_t columns = base.dimension();
    NodeList nodes_new;

    nodes_new.push_back(std::make_shared<Vector2D>(*line.nodes[0]));

    // Influence Matrices
    Eigen::MatrixXd A1(rows, columns-2); // nodes influence vector
    Eigen::MatrixXd A2(rows, 2);  // start/end point

    for (size_t row=0; row<rows; row++) {
        // p_0 [A1...] p_columns
        for (size_t column=1; column<columns-1; column++) {
            auto coeff = base.get(column, (double)row/(rows-1));
            A1(row, column-1) = coeff;
        }

        A2(row, 0) = base.get(0, (double)row/(rows-1));
        A2(row, 1) = base.get(columns-1, (double)row/(rows-1));
    }

    // result
    Eigen::MatrixXd p1(2, rows);
    Eigen::MatrixXd p2(2, 2);

    for (size_t dim=0; dim<2; dim++) {
        for (size_t column=0; column<rows; column++) {
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

    for (size_t i=0; i<columns-2; i++) {
        auto vector = std::make_shared<Vector2D>();
        for (size_t dim=0; dim<2; dim++) {
            vector->set_item(dim, solution(dim, i));
        }
        nodes_new.push_back(vector);
    }

    nodes_new.push_back(std::make_shared<Vector2D>(*line.nodes.back()));

    return T(PolyLine2D(nodes_new));
}

template class SplineCurve<BezierBase, BezierCurve>;
template class SplineCurve<BSplineBase<2>, BSplineCurve>;


template<typename SplineClass, typename T>
SymmetricSpline<SplineClass, T>::SymmetricSpline(PolyLine2D controlpoints) : controlpoints(controlpoints), spline_curve(controlpoints) {}


template<typename SplineClass, typename T>
T SymmetricSpline<SplineClass, T>::copy() const {
    return T(this->controlpoints);
}

template<typename SplineClass, typename T>
Vector2D SymmetricSpline<SplineClass, T>::get(double x) {
    this->apply();
    //return this->spline_curve.get(x);
    return this->spline_curve.get(0.5+x/2);
}


template<typename SplineClass, typename T>
PolyLine2D SymmetricSpline<SplineClass, T>::get_sequence(size_t segments) {
    this->apply();

    std::vector<std::shared_ptr<Vector2D>> nodes_new;

    for (size_t i=0; i<=segments; i++) {
        nodes_new.push_back(std::make_shared<Vector2D>(
            this->spline_curve.get(0.5+static_cast<double>(i)/(2*segments))
            //this->spline_curve.get(static_cast<double>(i)/segments)
            ));
    }

    return PolyLine2D(nodes_new);


}


template<typename SplineClass, typename T>
void SymmetricSpline<SplineClass, T>::apply() {
    Vector2D p1(0,0);
    Vector2D p2(0,1);
    auto line_1 = this->controlpoints.mirror(p1, p2);
    auto line_2 = this->controlpoints.copy();
    size_t numpoints = line_1.nodes.size();
    std::vector<std::shared_ptr<Vector2D>> nodes_new;

    for (size_t i=0; i<numpoints; i++) {
        nodes_new.insert(nodes_new.begin(), line_1.nodes[i]);
        nodes_new.push_back(line_2.nodes[i]);
    }

    this->spline_curve.controlpoints = PolyLine2D(nodes_new);    
}

template<typename SplineClass, typename T>
T SymmetricSpline<SplineClass, T>::fit(const PolyLine2D& nodes, size_t node_num) {
    Vector2D p1(0,0);
    Vector2D p2(0,1);
    auto line_1 = nodes.mirror(p1, p2);
    auto line_2 = nodes.copy();
    size_t numpoints = line_1.nodes.size();
    std::vector<std::shared_ptr<Vector2D>> nodes_new;

    nodes_new.push_back(line_1.nodes[0]);
    nodes_new.push_back(line_2.nodes[0]);
    if ((*line_2.nodes[0]-*line_1.nodes[0]).length() > 1e-6) {
    }

    for (size_t i=1; i<numpoints; i++) {
        nodes_new.insert(nodes_new.begin(), line_1.nodes[i]);
        nodes_new.push_back(line_2.nodes[i]);
    }

    auto polyline_new = PolyLine2D(nodes_new);

    for (auto node: nodes_new) {
        std::cout << "node" << node->get_item(0) << "/" << node->get_item(1) << std::endl;
    }

    //std::cout << polyline_new << std::endl;
    
    auto spline_curve = SplineClass::fit(polyline_new, 2*node_num);

    std::vector<std::shared_ptr<Vector2D>> controlpoints_new;
    for (size_t i=0; i<node_num; i++) {
        controlpoints_new.push_back(spline_curve.controlpoints.nodes[node_num+i]);
    }

    return T(controlpoints_new);
}


template class SymmetricSpline<BSplineCurve, SymmetricBSplineCurve>;