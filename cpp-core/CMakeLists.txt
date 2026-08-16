cmake_minimum_required(VERSION 3.20)
project(lance_duckdb_core CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Configure JNI compilation flags and track hardware includes
set(JAVA_HOME "/usr/lib/jvm/java-17-openjdk-amd64")
include_directories(${JAVA_HOME}/include)

# Configure OS specific sub-include paths for cross-platform stability
if(APPLE)
    include_directories(${JAVA_HOME}/include/darwin)
elseif(WIN32)
    include_directories(${JAVA_HOME}/include/win32)
else()
    include_directories(${JAVA_HOME}/include/linux)
endif()

include_directories(include)

# Compile library targets as shared binary structures
add_library(lance_duckdb_core SHARED src/lance_duckdb_core.cpp)

# Instruct compiler to emit clean performance warnings
target_compile_options(lance_duckdb_core PRIVATE -O3 -Wall)
