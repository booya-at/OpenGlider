set(CMAKE_SOURCE_DIR ${CMAKE_SOURCE_DIR}/src)
INCLUDE_DIRECTORIES(${CMAKE_SOURCE_DIR})

set(CPP_FILES
        mesh/mesh.cpp
        euklid/transform.cpp
        euklid/vector/vector.cpp
        euklid/polyline/polyline.cpp
        euklid/polyline/polyline_2d.cpp
        euklid/polyline/interpolation.cpp
        euklid/spline/basis.cpp
        euklid/spline/spline.cpp
        mesh/mesh.cpp
        )

set(HEADER_FILES
        mesh/mesh.hpp
        euklid/transform.hpp
        euklid/vector/vector.hpp
        euklid/polyline/polyline.hpp
        euklid/polyline/polyline_2d.hpp
        euklid/polyline/interpolation.hpp
        euklid/spline/basis.hpp
        euklid/spline/spline.hpp
        )

#ADD_SUBDIRECTORY(euklid)
pybind11_add_module(openglider_cpp pybind.cpp ${CPP_FILES} ${HEADER_FILES})

if(OpenMP_CXX_FOUND)
    target_link_libraries(openglider_cpp PUBLIC OpenMP::OpenMP_CXX)
endif()

target_link_libraries(openglider_cpp PUBLIC Eigen3::Eigen)
#if(OpenMP_CXX_FOUND)
#    target_link_libraries(gpufem_cpp PUBLIC OpenMP::OpenMP_CXX)
#endif()