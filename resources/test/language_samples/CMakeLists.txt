cmake_minimum_required(VERSION 3.15)

# Project definition
project(SampleProject 
    VERSION 1.0.0
    DESCRIPTION "A sample CMake project"
    LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Compiler-specific options
if(MSVC)
    target_compile_options(main PRIVATE /W4)
else()
    target_compile_options(main PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Find packages
find_package(Threads REQUIRED)

# Include directories
include_directories(include)

# Source files
set(SOURCES
    src/main.cpp
    src/utils.cpp
    src/person.cpp
)

# Create executable
add_executable(main ${SOURCES})

# Link libraries
target_link_libraries(main 
    PRIVATE 
        Threads::Threads
)

# Install rules
install(TARGETS main
    DESTINATION bin
)

# Testing
enable_testing()
add_subdirectory(tests)

# Custom target
add_custom_target(docs
    COMMAND doxygen Doxyfile
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Generating documentation"
) 