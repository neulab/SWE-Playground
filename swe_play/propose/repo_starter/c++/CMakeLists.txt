# Need modification

# Require a minimum version of CMake
cmake_minimum_required(VERSION 3.16)

# Define the project name
project(MyCppProject)

# Set the C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add the executable and its source files
add_executable(my_app main.cpp)