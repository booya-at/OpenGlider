#pragma once

#include<vector>
#include <algorithm>    // std::max
#include <memory>

#include "euklid/vector_3d.hpp"
#include "euklid/vector_2d.hpp"


template<typename T>
    class PolyLine {
        public:
            PolyLine();
            PolyLine(std::vector<std::shared_ptr<T>>&);

            std::shared_ptr<T> get(double ik);

            std::shared_ptr<T> __getitem__(int i);
            void __setitem__(std::shared_ptr<T> item);

            int __len__();
            float get_length();
            std::vector<std::shared_ptr<T>> get_segments();

            std::vector<std::shared_ptr<T>> nodes;
        
        private:
            std::string hash;
            
    };


class PolyLine2D : public PolyLine<Vector2D> {
    public:
        bool validate();
};