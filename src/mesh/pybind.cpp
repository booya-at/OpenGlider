#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "mesh.hpp"

namespace openglider::mesh {

    void REGISTER(pybind11::module m) {
        // test_nested_modules
        pybind11::module m_sub = m.def_submodule("mesh");
        

        m_sub.def("find_duplicates", &mesh::find_duplicates);
    }


}