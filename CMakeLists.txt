cmake_minimum_required(VERSION 3.10)
# --- Project Definition ---
project(SovereignAudioIngest
    VERSION 1.0.0
    LANGUAGES CXX)


set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# --- Executable Definition ---
add_executable(SovereignAudioIngest sovereign_render.cpp)

# --- Target Properties ---
target_include_directories(SovereignAudioIngest PRIVATE
    ${PROJECT_SOURCE_DIR}
)
