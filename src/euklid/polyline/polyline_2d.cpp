#include "polyline_2d.hpp"
#include "polyline.cpp"
//#include "common.cpp"


PolyLine2D PolyLine2D::normvectors() {
    auto segments = this->get_segments();
    std::vector<std::shared_ptr<Vector2D>> segment_normals;
    std::vector<std::shared_ptr<Vector2D>> normvectors;

    for (auto segment: segments) {
        auto normal = std::make_shared<Vector2D>();
        
        normal->set_item(0, segment->get_item(1));
        normal->set_item(1, -segment->get_item(0));
        normal->normalize();
        segment_normals.push_back(normal);
    }

    normvectors.push_back(segment_normals[0]);

    
    for (unsigned int i=0; i<segment_normals.size()-1; i++) {
        Vector2D normal = (*segment_normals[i] + *segment_normals[i+1]);
        normal.normalize();
        //auto normal = segment_normals[i]->copy();

        normvectors.push_back(std::make_shared<Vector2D>(normal));
    }
    

    normvectors.push_back(segment_normals.back());

    return PolyLine2D(normvectors);
}

PolyLine2D PolyLine2D::offset(double amount) {
    auto normvectors = this->normvectors().nodes;
    std::vector<std::shared_ptr<Vector2D>> nodes;

    for (unsigned int i=0; i<this->nodes.size(); i++) {
        nodes.push_back(std::make_shared<Vector2D>(*this->nodes[i] + (*normvectors[i])*amount));
    }

    return PolyLine2D(nodes);
}

std::vector<std::pair<double, double>> PolyLine2D::cut(Vector2D& p1, Vector2D& p2) {
    std::vector<std::pair<double, double>> results;
    if (this->nodes.size() < 2) {
        return results;
    }

    // cut first segment
    auto result = cut_2d(*this->nodes[0], *this->nodes[1], p1, p2);

    
    if (result.success && result.ik_1 <= 0) {
        results.push_back(std::pair<double, double>(result.ik_1, result.ik_2));
    }

    // try all segments
    for (unsigned int i=0; i<this->nodes.size()-1; i++) {
        result = cut_2d(*this->nodes[i], *this->nodes[i+1], p1, p2);

        if (result.success && 0. < result.ik_1 && result.ik_1 <= 1.) {
            results.push_back(std::pair<double, double>(result.ik_1+i, result.ik_2));
        }
    }

    // add value if for the last cut ik_1 is greater than 1 (extrapolate end)
    if (result.success && result.ik_1 > 1) {
            results.push_back(std::pair<double, double>(result.ik_1+this->nodes.size()-2, result.ik_2));
    }

    return results;

}

std::pair<double, double> PolyLine2D::cut(Vector2D& v1, Vector2D& v2, const double nearest_ik) {
    using cut = std::pair<double, double>;
    auto cuts = this->cut(v1, v2);
    
    std::sort(cuts.begin(), cuts.end(), [nearest_ik](cut& a, cut& b) {
        return std::abs(a.first-nearest_ik) < std::abs(b.first-nearest_ik);
    });

    return cuts[0];
}


PolyLine2D PolyLine2D::fix_errors() {
    if (this->nodes.size() <= 4) {
        return this->copy();
    }
    for (unsigned int i=0; i<this->nodes.size()-3; i++) {
        int new_list_start = i+2;
        auto nodes2 = std::vector<std::shared_ptr<Vector2D>>(this->nodes.begin() + new_list_start, this->nodes.end());
        PolyLine2D line2 = PolyLine2D(nodes2);

        auto cuts = line2.cut(*this->nodes[i], *this->nodes[i+1]);
        // start from the back
        std::reverse(cuts.begin(), cuts.end());

        for (auto result: cuts) {
            if (0 <= result.first && result.first < line2.nodes.size()-1-1e-10 && 0 <= result.second && result.second < 1) {
                
                std::vector<std::shared_ptr<Vector2D>> new_nodes;
                // new line: 0 to i and result to end
                for (unsigned int j=0; j<=i; j++) {
                    new_nodes.push_back(std::make_shared<Vector2D>(*this->nodes[j]));
                }
                
                new_nodes.push_back(line2.get(result.first));

                int start_2 = int(result.first) + 1;

                if (std::abs(result.first-start_2) < 1e-5) {
                    start_2 += 1;
                }

                
                for (unsigned int j=start_2; j<line2.nodes.size(); j++) {
                    new_nodes.push_back(std::make_shared<Vector2D>(*line2.nodes[j]));
                }

                return PolyLine2D(new_nodes).fix_errors();
            }
        }
        
    }

    // no cuts found -> remove zero-length segments

    std::vector<std::shared_ptr<Vector2D>> nodes_new;
    // Remove len-0 segment points
    auto segment_lengthes = this->get_segment_lengthes();
    nodes_new.push_back(std::make_shared<Vector2D>(*this->nodes[0]));

    for (unsigned int i=0; i<segment_lengthes.size(); i++){
        if (segment_lengthes[i] > 1e-5) {
            nodes_new.push_back(std::make_shared<Vector2D>(*this->nodes[i+1]));
        }
    }

    return PolyLine2D(nodes_new);
}


PolyLine2D PolyLine2D::mirror(Vector2D& p1, Vector2D& p2) {
    auto diff = p1 - p2;
    auto normvector = Vector2D(-diff[1], diff[0]);
    std::vector<std::shared_ptr<Vector2D>> result;

    for (auto node: this->nodes) {
        result.push_back(std::make_shared<Vector2D>(
            *node - normvector * (2 * normvector.dot(*node-p1))
        ));
    }

    return PolyLine2D(result);
}


PolyLine2D PolyLine2D::rotate(double radians, Vector2D& origin) {
    std::vector<std::shared_ptr<Vector2D>> new_nodes;
    auto rotation = Rotation2D(radians);

    for (auto node: this->nodes) {
        new_nodes.push_back(std::make_shared<Vector2D>(origin + rotation.apply(*node - origin)));
    }

    return PolyLine2D(new_nodes);
}


PolyLine3D PolyLine2D::to_3d() const {
    std::vector<std::shared_ptr<Vector3D>> new_nodes;

    return PolyLine3D();

    
}


template class PolyLine<Vector2D, PolyLine2D>;
//std::pair<std::shared_ptr<Vector2D>>