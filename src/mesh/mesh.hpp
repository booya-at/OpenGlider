#pragma once

#include<string> // for string class 
#include <set>
#include <vector>
#include <memory>
#include "euklid/vector/vector.hpp"

namespace openglider::mesh {

    using match_vector = std::vector<std::tuple<int, int>>;

    template<typename proptype>
    class PropertyList {
        public:
            PropertyList();
            std::vector<std::pair<std::string, proptype>> values;

            void set_value(std::string, proptype);
            proptype get_value(std::string);
            void merge(PropertyList<proptype>&);
    };

    class MeshVector : public Vector3D {
        public:
            PropertyList<int> properties_int;
            PropertyList<float> properties_float;
            PropertyList<bool> properties_bool;

            void merge_props(MeshVector&);
    };


    using VectorList = std::vector<std::shared_ptr<MeshVector>>;

    class MeshEntity {
        public:
            std::vector<std::shared_ptr<MeshVector>> nodes;

            PropertyList<int> properties_int;
            PropertyList<float> properties_float;
            PropertyList<bool> properties_bool;
    };

    class MeshLayer {
        public:
            MeshLayer();
            MeshLayer(std::vector<std::shared_ptr<MeshEntity>>);

            std::vector<std::shared_ptr<MeshEntity>> polygons;
    };
    

    class Mesh {
        public:
            Mesh();
            Mesh(std::vector<std::shared_ptr<MeshLayer>>);

            std::vector<std::shared_ptr<MeshLayer>> layers;
            std::vector<std::shared_ptr<MeshEntity>> boundaries;

            VectorList get_nodes();
            //std::pair<VectorList, std::vector<std::vector<int>>> get_indexed();
            //int delete_duplicates();
    };
    

    match_vector find_duplicates(std::vector<std::shared_ptr<Vector3D>> points, float max_distance=0.0001);
}
