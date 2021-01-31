#include "euklid/spline/basis.hpp"


size_t choose(size_t n, size_t k) {
    if (k <= n) {
        size_t ntok = 1;
        size_t ktok = 1;
        size_t range = std::min(k, n-k) + 1;

        for (size_t t=1; t < range; t++) {
            ntok *= n;
            ktok *= t;
            n -= 1;
        }
        return ntok / ktok;
    } else {
        return 0;
    }
}


BezierBase::BezierBase(size_t size) {
    for (size_t i=0; i<size; i++) {
        size_t k = choose(size-1, i);
        this->bases.push_back([size, i, k](double x) {
            return k * pow(x, (double)i) * pow(1.-x, (double)(size - 1 - i));
        });
    }
}

size_t BezierBase::dimension() const {
    return this->bases.size();
}

double BezierBase::get(size_t index, double value) const {
    if (index >= this->bases.size()) {
        throw std::exception();
    }
    return this->bases[index](value);
}

template<size_t degree>
BSplineBase<degree>::BSplineBase(size_t size) {

    // create knots
    size_t total_knots = size + degree + 1;
    size_t inner_knots = total_knots - 2*degree;

    for (size_t i=0; i<degree; i++) {
        this->knots.push_back(0.);
    }
    for (size_t i=0; i<inner_knots; i++) {
        this->knots.push_back((double)i/(inner_knots-1));
    }
    for (size_t i=0; i<degree; i++) {
        this->knots.push_back(1.);
    }


    for (size_t i=0; i<size; i++) {
        this->bases.push_back(this->get_basis(degree, i));
    }

}


template<size_t degree>
std::function<double(double)> BSplineBase<degree>::get_basis(size_t basis_degree, size_t index) {
    if (basis_degree <= 0) {
        return [knots = this->knots, index](double x){
            if (knots[index] < x && x <= knots[index+1]) {
                return 1.;
            }
            return 0.;
        };
    } else {
        auto next_basis_1 = this->get_basis(basis_degree-1, index);
        auto next_basis_2 = this->get_basis(basis_degree-1, index+1);
        return [knots = this->knots, basis_degree, index, next_basis_1, next_basis_2](double x){
            if (index==0 && x <= 0.) {
                return 1.;
            } else {
                double out = 0.;

                double t_this = knots[index];
                double t_next = knots[index+1];
                double t_precog = knots[index+basis_degree];
                double t_horizon = knots[index+basis_degree+1];

                double top = (x-t_this);
                double bottom = (t_precog - t_this);

                if (bottom != 0) {
                    out = top/bottom * next_basis_1(x);
                }

                top = t_horizon-x;
                bottom = t_horizon-t_next;

                if (bottom > 1e-8) {
                    out += top/bottom * next_basis_2(x);
                }


                return out;
            }
        };

    }
}

template<size_t degree>
double BSplineBase<degree>::get(size_t index, double value) const { 
    if (index >= this->bases.size()) {
        throw std::exception();
    }
    return this->bases[index](value);
 }


template<size_t degree>
size_t BSplineBase<degree>::dimension() const {
    return this->bases.size();
}


template class BSplineBase<2>;