#include "euklid/spline/basis.hpp"


unsigned int choose(unsigned int n, unsigned int k) {
    if (k <= n) {
        unsigned int ntok = 1;
        unsigned int ktok = 1;
        unsigned int range = std::min(k, n-k) + 1;

        for (unsigned int t=1; t < range; t++) {
            ntok *= n;
            ktok *= t;
            n -= 1;
        }
        return ntok / ktok;
    } else {
        return 0;
    }
}


BezierBase::BezierBase(unsigned int size) {
    for (unsigned int i=0; i<size; i++) {
        unsigned int k = choose(size-1, i);
        this->bases.push_back([size, i, k](double x) {
            return k * pow(x, (double)i) * pow(1.-x, (double)(size - 1 - i));
        });
    }
}

unsigned int BezierBase::dimension() const {
    return this->bases.size();
}

double BezierBase::get(unsigned int index, double value) const {
    if (index >= this->bases.size()) {
        throw std::exception();
    }
    return this->bases[index](value);
}

template<unsigned int degree>
BSplineBase<degree>::BSplineBase(unsigned int size) {

    // create knots
    uint total_knots = size + degree + 1;
    uint inner_knots = total_knots - 2*degree;

    for (uint i=0; i<degree; i++) {
        this->knots.push_back(0.);
    }
    for (uint i=0; i<inner_knots; i++) {
        this->knots.push_back((double)i/(inner_knots-1));
    }
    for (uint i=0; i<degree; i++) {
        this->knots.push_back(1.);
    }


    for (unsigned int i=0; i<size; i++) {
        this->bases.push_back(this->get_basis(degree, i));
    }

}


template<unsigned int degree>
std::function<double(double)> BSplineBase<degree>::get_basis(unsigned int basis_degree, unsigned int index) {
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

template<unsigned int degree>
double BSplineBase<degree>::get(unsigned int index, double value) const { 
    if (index >= this->bases.size()) {
        throw std::exception();
    }
    return this->bases[index](value);
 }


template<unsigned int degree>
unsigned int BSplineBase<degree>::dimension() const {
    return this->bases.size();
}


template class BSplineBase<2>;