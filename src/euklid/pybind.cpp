#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>

#include <vector>
#include "euklid/vector/vector.hpp"
#include "euklid/vector/cut_2d.hpp"
#include "euklid/vector/translation.hpp"
#include "euklid/polyline/polyline.hpp"
#include "euklid/polyline/polyline_2d.hpp"

namespace py = pybind11;
using namespace py::literals;

template<typename list_type, typename VectorT>
std::vector<std::shared_ptr<VectorT>> get_vector_list(list_type lst) {
    std::vector<std::shared_ptr<VectorT>> result;

    for (long unsigned int i=0; i<py::len(lst); i++) {
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
py::class_<VectorType, std::shared_ptr<VectorType>> PyVector(py::module_ m, const char *name) {
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
            .def("__str__", [](const VectorType &v) {
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

template<typename PolyLineType, typename VectorClass>
py::class_<PolyLineType> PyPolyLine(py::module_ m, const char *name) {
    return py::class_<PolyLineType>(m, name)
        .def(py::init([](py::list t)
        {
            auto lst = get_vector_list<py::list, VectorClass>(t);
            return PolyLineType(lst);
        }))
        .def("__len__", &PolyLineType::__len__)
            .def("__iter__", [](const PolyLineType& v){
                return py::make_iterator(v.nodes.begin(), v.nodes.end());
            })
        .def("copy", &PolyLineType::copy)
        .def("__copy__",  [](PolyLineType& self) {
            return self.copy();
        })
        .def("__deepcopy__", [](PolyLineType& self, py::dict) {
            return self.copy();
        }, "memo"_a)
        .def("get", py::overload_cast<const double>(&PolyLineType::get))
        .def("get", py::overload_cast<const double, const double>(&PolyLineType::get))
        .def("get_segments", &PolyLineType::get_segments)
        .def("get_segment_lengthes", &PolyLineType::get_segment_lengthes)
        .def("get_length", &PolyLineType::get_length)
        .def("walk", &PolyLineType::walk)
        .def("resample", &PolyLineType::resample)
        .def("scale", py::overload_cast<const double>(&PolyLineType::scale))
        .def("scale", py::overload_cast<const VectorClass&>(&PolyLineType::scale))
        .def("move", &PolyLineType::move)
        .def("__mul__", py::overload_cast<const double>(&PolyLineType::scale))
        .def("__mul__", py::overload_cast<const VectorClass&>(&PolyLineType::scale))
        .def(py::self + py::self)
        .def("reverse", &PolyLineType::reverse)
        .def("mix", &PolyLineType::mix)
        .def_readonly("nodes", &PolyLineType::nodes);
}

namespace openglider::euklid {

    void REGISTER(pybind11::module module) {
        pybind11::module m = module.def_submodule("euklid");


        m.def("cut", &cut_2d);
        py::class_<Rotation2D>(m, "Rotation2D")
            .def(py::init<double>())
            .def("apply", &Rotation2D::apply);

        py::class_<Translation>(m, "Translation")
            .def(py::init<>())
            .def_readonly("matrix", &Translation::matrix)
            .def_static("rotation", &Translation::rotation)
            .def_static("translation", py::overload_cast<const Vector3D&>(&Translation::translation))
            .def_static("translation", py::overload_cast<const Vector2D&>(&Translation::translation))
            .def_static("scale", &Translation::scale)
            .def("apply", py::overload_cast<const Vector3D&>(&Translation::apply, py::const_))
            .def("apply", py::overload_cast<const Vector2D&>(&Translation::apply, py::const_))
            .def("chain", &Translation::chain);

        py::class_<CutResult>(m, "CutResult")
            .def_readonly("success", &CutResult::success)
            .def_readonly("ik_1", &CutResult::ik_1)
            .def_readonly("ik_2", &CutResult::ik_2)
            .def_readonly("point", &CutResult::point);

        PyVector<Vector3D>(m, "Vector3D");
            //.def_readwrite("z", &Vector3D::z);

        py::implicitly_convertible<py::tuple, Vector3D>();
        py::implicitly_convertible<py::list,  Vector3D>();

        PyVector<Vector2D>(m, "Vector2D")
            .def("cross", &Vector2D::cross);

        py::implicitly_convertible<py::tuple, Vector2D>();
        py::implicitly_convertible<py::list,  Vector2D>();

        PyPolyLine<PolyLine3D, Vector3D>(m, "PolyLine3D");
        
        PyPolyLine<PolyLine2D, Vector2D>(m, "PolyLine2D")
            .def("rotate", &PolyLine2D::rotate)
            .def("normvectors", &PolyLine2D::normvectors)
            .def("offset", &PolyLine2D::offset)
            .def("mirror", &PolyLine2D::mirror)
            .def("cut", py::overload_cast<Vector2D&, Vector2D&>(&PolyLine2D::cut))
            .def("cut", py::overload_cast<Vector2D&, Vector2D&, const double>(&PolyLine2D::cut))
            .def("fix_errors", &PolyLine2D::fix_errors);
    }
}