#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>

#include <vector>
#include "euklid/vector/vector.hpp"
#include "euklid/vector/cut_2d.hpp"
#include "euklid/polyline/polyline.hpp"
#include "euklid/polyline/polyline_2d.hpp"

namespace py = pybind11;
using namespace py::literals;

template<typename list_type, typename VectorT>
std::vector<std::shared_ptr<VectorT>> get_vector_list(list_type lst) {
    std::vector<std::shared_ptr<VectorT>> result;

    for (int i=0; i<py::len(lst); i++) {
        list_type lst_i = lst[i];
        if (py::len(lst_i) != VectorT::dimension)
            throw std::runtime_error("Should have length 3.");

        auto vec = std::make_shared<VectorT>();

        for (int j=0; j<VectorT::dimension; j++){
            double value = lst_i[j].template cast<double>();
            vec->set_item(j, value);
        }
        result.push_back(vec);
    }

    return result;
}

template<typename VectorType>
py::class_<VectorType, std::shared_ptr<VectorType>> vectorClass(py::module_ m, const char *name) {
    return py::class_<VectorType, std::shared_ptr<VectorType>>(m, name)
            .def(py::init([](py::tuple t)
                {
                    if (py::len(t) != VectorType::dimension)
                        throw std::runtime_error("Should have length 3.");
                    
                    auto vec = VectorType();

                    for (int i=0; i<VectorType::dimension; i++) {
                        vec.set_item(i, t[i].cast<double>());
                    }
                    return vec;
                }))
            .def(py::init([](py::list t)
                {
                    if (py::len(t) != VectorType::dimension)
                        throw std::runtime_error("Should have length 3.");
                    
                    auto vec = VectorType();

                    for (int i=0; i<VectorType::dimension; i++) {
                        vec.set_item(i, t[i].cast<double>());
                    }
                    return vec;
                }))        
            //.def_readwrite("x", &VectorType::x)
            //.def_readwrite("y", &VectorType::y)
            .def("__getitem__", [](const VectorType &v, size_t i) {
                    return v.get_item(i);
            })
            .def("__setitem__", [](VectorType &v, size_t i, double value){
                v.set_item(i, value);
            })
            .def("__len__", [](const VectorType& v) {return v.dimension;})
            .def("__iter__", [](const VectorType& v){
                return py::make_iterator(v.coordinates, v.coordinates+v.dimension);
            })
            .def("__str__", [name](const VectorType &v) {
                std::string out;
                out += "(";
                for (int i=0; i<VectorType::dimension; i++) {
                    out += "{:.4} "_s.format(v.get_item(i));
                }
                out.resize(out.size()-1);
                out += ")";
                return out;
            })
            .def("__repr__", [name](const VectorType &v) {
                std::string out = name;
                out += "(";
                for (int i=0; i<VectorType::dimension; i++) {
                    out += "{:.4} "_s.format(v.get_item(i));
                }
                out.resize(out.size()-1);
                out += ")";
                return out;
            })
            .def(py::self + py::self)
            .def(py::self - py::self)
            .def(py::self * double())
            .def("dot", &VectorType::dot)
            .def("length", &VectorType::length)
            .def("copy", &VectorType::copy)
            .def("normalize", &VectorType::normalize);
}

namespace openglider::euklid {

    void REGISTER(pybind11::module module) {
        pybind11::module m = module.def_submodule("euklid");


        m.def("cut", &cut_2d);
        py::class_<CutResult>(m, "CutResult")
            .def_readonly("success", &CutResult::success)
            .def_readonly("ik_1", &CutResult::ik_1)
            .def_readonly("ik_2", &CutResult::ik_2)
            .def_readonly("point", &CutResult::point);

        vectorClass<Vector3D>(m, "Vector3D");
            //.def_readwrite("z", &Vector3D::z);

        py::implicitly_convertible<py::tuple, Vector3D>();
        py::implicitly_convertible<py::list,  Vector3D>();

        vectorClass<Vector2D>(m, "Vector2D");

        py::implicitly_convertible<py::tuple, Vector2D>();
        py::implicitly_convertible<py::list,  Vector2D>();

        py::class_<PolyLine3D>(m, "PolyLine3D")
            .def(py::init([](py::list t)
            {
                auto lst = get_vector_list<py::list, Vector3D>(t);
                return PolyLine3D(lst);
            }))
            .def("__len__", &PolyLine3D::__len__)
            .def("get", &PolyLine3D::get)
            .def("get_segments", &PolyLine3D::get_segments)
            .def("get_segment_lengthes", &PolyLine3D::get_segment_lengthes)
            .def("get_length", &PolyLine3D::get_length)
            .def("walk", &PolyLine3D::walk)
            .def("resample", &PolyLine3D::resample)
            .def_readonly("nodes", &PolyLine3D::nodes);
        
        py::class_<PolyLine2D>(m, "PolyLine2D")
            .def(py::init([](py::list t)
            {
                auto lst = get_vector_list<py::list, Vector2D>(t);
                return PolyLine2D(lst);
                //return PolyLine2D();
            }))
            .def("__len__", &PolyLine2D::__len__)
            .def("get", &PolyLine2D::get)
            .def("get_segments", &PolyLine2D::get_segments)
            .def("get_segment_lengthes", &PolyLine2D::get_segment_lengthes)
            .def("get_length", &PolyLine2D::get_length)
            .def("walk", &PolyLine2D::walk)
            .def("resample", &PolyLine2D::resample)
            .def("normvectors", &PolyLine2D::normvectors)
            .def("offset", &PolyLine2D::offset)
            .def("cut", &PolyLine2D::cut)
            .def("fix_errors", &PolyLine2D::fix_errors)
            .def_readonly("nodes", &PolyLine2D::nodes);
    };
}