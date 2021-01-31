#pragma once

#include<vector>
#include <algorithm>    // std::max
#include <memory>

#include "euklid/vector/vector.hpp"
#include "euklid/vector/transform.hpp"


template<typename VectorType, typename T>
    class PolyLine {
        public:
            PolyLine();
            PolyLine(std::vector<std::shared_ptr<VectorType>>&);

            std::shared_ptr<VectorType> get(double ik) const;
            T get(double ik_start, double ik_end) const;

            int numpoints();
            double get_length();
            std::vector<std::shared_ptr<VectorType>> get_segments();
            std::vector<double> get_segment_lengthes();
            
            double walk(double start, double amount);

            std::vector<std::shared_ptr<VectorType>> nodes;

            T resample(const int num_points);
            T reverse();
            T copy() const;
            T scale(const VectorType&);
            T scale(const double);
            T mix(T&, const double);
            T move(const VectorType&) const;

            T transform(const Transformation&) const;

            T operator+ (const T&) const;
        
        private:
            std::string hash;
            
    };

class PolyLine3D : public PolyLine<Vector3D, PolyLine3D> {
    public:
        using PolyLine<Vector3D, PolyLine3D>::PolyLine;
};
