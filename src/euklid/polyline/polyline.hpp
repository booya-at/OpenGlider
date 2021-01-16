#pragma once

#include<vector>
#include <algorithm>    // std::max
#include <memory>

#include "euklid/vector/vector_3d.hpp"
#include "euklid/vector/vector_2d.hpp"


template<typename VectorType>
    class PolyLine {
        public:
            PolyLine();
            PolyLine(std::vector<std::shared_ptr<VectorType>>&);

            std::shared_ptr<VectorType> get(double ik);

            std::shared_ptr<VectorType> __getitem__(int i);
            void __setitem__(std::shared_ptr<VectorType> item);

            int __len__();
            float get_length();
            std::vector<std::shared_ptr<VectorType>> get_segments();
            std::vector<double> get_segment_lengthes();
            
            double walk(double start, double amount);

            std::vector<std::shared_ptr<VectorType>> nodes;
        
        private:
            std::string hash;
            
    };

class PolyLine3D : public PolyLine<Vector3D> {
    public:
        using PolyLine<Vector3D>::PolyLine;
        PolyLine3D resample(int num_points);
};
