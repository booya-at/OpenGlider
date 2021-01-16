
template<typename PolyLineClass, typename VectorClass>
PolyLineClass resample_template(PolyLineClass *self, int num_points) {
    float distance = self->get_length() / (num_points-1);
    float ik = 0;
    std::vector<std::shared_ptr<VectorClass>> nodes_new;

    nodes_new.push_back(self->get(0.));
    
    for (int i=0; i<num_points-2; i++) {
        ik = self->walk(ik, distance);
        nodes_new.push_back(self->get(ik));
    }

    nodes_new.push_back(std::make_shared<VectorClass>(*self->nodes.back()));

    return PolyLineClass(nodes_new);
}