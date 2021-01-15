#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <vector>
#include "vector_3d.hpp"
#include "vector_2d.hpp"
#include "polyline.hpp"

namespace py = pybind11;
using namespace py::literals;

std::vector<std::shared_ptr<Vector3D>> get_vector_3_list(py::list lst) {
    std::vector<std::shared_ptr<Vector3D>> result;

    for (int i=0; i<py::len(lst); i++) {
        py::list lst_i = lst[i];
        if (py::len(lst_i) != 3)
            throw std::runtime_error("Should have length 3.");

        result.push_back(std::make_shared<Vector3D>(
            lst_i[0].cast<double>(), lst_i[1].cast<double>(), lst_i[2].cast<double>()
        ));
    }

    return result;
}

std::vector<std::shared_ptr<Vector2D>> get_vector_2_list(py::list lst) {
    std::vector<std::shared_ptr<Vector2D>> result;

    for (int i=0; i<py::len(lst); i++) {
        py::list lst_i = lst[i];
        if (py::len(lst_i) != 2)
            throw std::runtime_error("Should have length 2.");

        result.push_back(std::make_shared<Vector2D>(
            lst_i[0].cast<double>(), lst_i[1].cast<double>()
        ));
    }

    return result;
}

namespace openglider::euklid {

    void REGISTER(pybind11::module module) {
        pybind11::module m = module.def_submodule("euklid");

        py::class_<Vector3D, std::shared_ptr<Vector3D>>(m, "Vector3D")
            .def(py::init([](py::tuple t)
            {
                if (py::len(t) != 3)
                    throw std::runtime_error("Should have length 3.");
                return Vector3D{t[0].cast<double>(), t[1].cast<double>(), t[2].cast<double>()};
            }))
            .def(py::init([](py::list t)
            {
                if (py::len(t) != 3)
                    throw std::runtime_error("Should have length 3.");
                return Vector3D{t[0].cast<double>(), t[1].cast<double>(), t[2].cast<double>()};
            }))        
            .def_readwrite("x", &Vector3D::x)
            .def_readwrite("y", &Vector3D::y)
            .def_readwrite("z", &Vector3D::z)
            .def("__getitem__", [](const Vector3D &v, size_t i)
            {
                if (i == 0) return v.x;
                if (i == 1) return v.y;
                if (i == 2) return v.z;
                throw py::index_error();
                return 0.d;
            })
            .def("__str__", [](const Vector3D &v) {
                return "({:.4}, {:.4}, {:.4})"_s.format(v.x, v.y, v.z);
            })
            .def("__repr__", [](const Vector3D &v) {
                return "Vector3D({:.4}, {:.4}, {:.4})"_s.format(v.x, v.y, v.z);
            })
            .def("__sub__", [](Vector3D &v1, Vector3D &v2){
                return v1 - v2;
            })
            .def("__add__", [](Vector3D &v1, Vector3D &v2){
                return v1 + v2;
            })
            .def("__mul__", [](Vector3D &v, double value){
                return v * value;
            })
            .def("length", &Vector3D::length);

        py::implicitly_convertible<py::tuple, Vector3D>();
        py::implicitly_convertible<py::list,  Vector3D>();

        py::class_<Vector2D, std::shared_ptr<Vector2D>>(m, "Vector2D")
            .def(py::init([](py::tuple t)
            {
                if (py::len(t) != 2)
                    throw std::runtime_error("Should have length 2.");
                return Vector2D{t[0].cast<double>(), t[1].cast<double>()};
            }))
            .def(py::init([](py::list t)
            {
                if (py::len(t) != 2)
                    throw std::runtime_error("Should have length 2.");
                return Vector2D{t[0].cast<double>(), t[1].cast<double>()};
            }))        
            .def_readwrite("x", &Vector2D::x)
            .def_readwrite("y", &Vector2D::y)
            .def("__getitem__", &Vector2D::get_item)
            .def("__str__", [](const Vector2D &v) {
                return "({:.4}, {:.4})"_s.format(v.x, v.y);
            })
            .def("__repr__", [](const Vector2D &v) {
                return "Vector2D({:.4}, {:.4})"_s.format(v.x, v.y);
            })
            .def("__sub__", [](Vector2D &v1, Vector2D &v2){
                return v1 - v2;
            })
            .def("__add__", [](Vector2D &v1, Vector2D &v2){
                return v1 + v2;
            })
            .def("__mul__", [](Vector2D &v, double value){
                return v * value;
            })
            .def("length", &Vector2D::length);

        py::implicitly_convertible<py::tuple, Vector2D>();
        py::implicitly_convertible<py::list,  Vector2D>();

        py::class_<PolyLine<Vector3D>>(m, "PolyLine3D")
            .def(py::init([](py::list t)
            {
                auto lst = get_vector_3_list(t);
                return PolyLine<Vector3D>(lst);
            }))
            .def("__len__", &PolyLine<Vector3D>::__len__)
            .def("get_segments", &PolyLine<Vector3D>::get_segments)
            .def("get_length", &PolyLine<Vector3D>::get_length)
            .def_readonly("nodes", &PolyLine<Vector3D>::nodes);
        
        py::class_<PolyLine2D>(m, "PolyLine2D")
            .def(py::init([](py::list t)
            {
                auto lst = get_vector_2_list(t);
                //return PolyLine2D(lst);
                return PolyLine2D();
            }))
            .def("__len__", &PolyLine2D::__len__)
            .def("get_segments", &PolyLine2D::get_segments)
            .def("get_length", &PolyLine2D::get_length)
            .def_readonly("nodes", &PolyLine2D::nodes);
    };
}