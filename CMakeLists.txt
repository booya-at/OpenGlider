CMAKE_MINIMUM_REQUIRED(VERSION 3.3)

PROJECT(openglider_cpp)

#set(CMAKE_C_COMPILER)
set(CMAKE_SOURCE_DIR ${CMAKE_SOURCE_DIR}/src)

set (CMAKE_CXX_STANDARD 20)
SET(CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake)
#SET(CMAKE_CXX_FLAGS_RELEASE "-O3")

# DEPENDENCIES

if(EXISTS ${PROJECT_SOURCE_DIR}/lib/pybind11)
    add_subdirectory(${PROJECT_SOURCE_DIR}/lib/pybind11)
else()
    find_package(pybind11 REQUIRED)
endif()
set(PYBIND11_CPP_STANDARD -std=c++14)


message(${PROJECT_SOURCE_DIR})
if(EXISTS ${PROJECT_SOURCE_DIR}/lib/eigen)
    add_subdirectory(${PROJECT_SOURCE_DIR}/lib/eigen)
else()
    find_package (Eigen3 3.3 REQUIRED NO_MODULE)
endif()

find_package(OpenMP)


# OPTIONS
OPTION(BUILD_PYTHON_BINDINGS "create python bindings" ON)

if (MSVC)
    # warning level 4 and all warnings as errors
    # add_compile_options(/W4 /WX)
else()
    # lots of warnings and all warnings as errors
    add_compile_options(-Wall -Wextra -pedantic -Werror)
endif()

ADD_SUBDIRECTORY("src" "openglider_cpp")

#ADD_SUBDIRECTORY("tests/")
