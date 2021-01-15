#include "mesh/mesh.hpp"

namespace openglider::mesh
{
    template<typename proptype>
    void PropertyList<proptype>::set_value(std::string key, proptype value) {
        for (auto item: this->values) {
            if (item.first == key) {
                // overwrite
                item.second = value;
                return;
            }
        }
        // not found
        this->values.push_back({key, value});
    };

    template<typename proptype>
    proptype PropertyList<proptype>::get_value(std::string key){
        for (auto item: this->values) {
            if (item.first == key) {
                return item.second;
            }
        }

        throw "Not found";
    };

    template<typename proptype>
    void PropertyList<proptype>::merge(PropertyList<proptype>& other) {
        for (auto item: other.values) {
            this->set_value(item.first, item.second);
        }
    };

    void MeshVector::merge_props(MeshVector& v2) {
        this->properties_bool.merge(v2.properties_bool);
        this->properties_float.merge(v2.properties_float);
        this->properties_int.merge(v2.properties_int);
    };

    Mesh::Mesh(std::vector<std::shared_ptr<MeshLayer>> layers) {
        this->layers = layers;
    }

    VectorList Mesh::get_nodes() {
        std::set<std::shared_ptr<MeshVector>> node_set;
        for (auto layer: this->layers) {

            for (auto poly: layer->polygons) {
                for (auto node: poly->nodes) {
                    node_set.insert(node);
                }
            }

        }
        VectorList out(node_set.begin(), node_set.end());
        return out;
    }

    match_vector find_duplicates(std::vector<std::shared_ptr<Vector3D>> points, float max_distance) {
        // https://stackoverflow.com/questions/24765180/parallelizing-a-for-loop-using-openmp-replacing-push-back

        match_vector global_matches;

        #pragma omp parallel
        {
            match_vector local_matches;

            #pragma omp for nowait
            for (int i = 0; i < points.size(); i++) {
                auto v1 = points[i];

                for (int j=i+1; j<points.size(); j++) {
                    if (v1->distance(*points[j]) < max_distance){
                        local_matches.push_back({i, j});
                    }
                }
            }
            #pragma omp critical
            global_matches.insert(global_matches.end(), local_matches.begin(), local_matches.end());
        }

        return global_matches;
    }
} // namespace openglider::mesh
