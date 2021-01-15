#include <pybind11/pybind11.h>
#include <vector>
#include <pybind11/stl.h>

#include "euklid/pybind.cpp"
#include "mesh/pybind.cpp"

namespace py = pybind11;
using namespace py::literals;


PYBIND11_MODULE(openglider_cpp, m) {
    m.doc() = "openglider python module";

    openglider::euklid::REGISTER(m);
    openglider::mesh::REGISTER(m);
}