set(CMAKE_SOURCE_DIR ${CMAKE_SOURCE_DIR}/src)
INCLUDE_DIRECTORIES(${CMAKE_SOURCE_DIR})

set(CPP_FILES
        euklid/vector/vector_3d.cpp
        euklid/vector/vector_2d.cpp
        euklid/polyline/polyline.cpp
        euklid/polyline/polyline_2d.cpp
        mesh/mesh.cpp
        )

set(HEADER_FILES
        euklid/vector/vector_3d.hpp
        euklid/vector/vector_2d.hpp
        euklid/polyline/polyline.hpp
        euklid/polyline/polyline_2d.hpp
        mesh/mesh.hpp
        )

pybind11_add_module(openglider_cpp pybind.cpp ${CPP_FILES} ${HEADER_FILES})

if(OpenMP_CXX_FOUND)
    target_link_libraries(openglider_cpp PUBLIC OpenMP::OpenMP_CXX)
endif()
#if(OpenMP_CXX_FOUND)
#    target_link_libraries(gpufem_cpp PUBLIC OpenMP::OpenMP_CXX)
#cendif()

#add_executable(test test.cpp ${CPP_FILES} ${HEADER_FILES})
#target_link_libraries(test PRIVATE ${OpenCL_LIBRARIES})

#add_executable(test2 test2.cpp)
#target_link_libraries(test2 PRIVATE ${OpenCL_LIBRARIES})

#file(COPY           ${CMAKE_CURRENT_SOURCE_DIR}/kernel_test.cl
#     DESTINATION    ${CMAKE_CURRENT_BINARY_DIR}
#     )