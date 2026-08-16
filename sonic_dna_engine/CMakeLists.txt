cmake_minimum_required(VERSION 3.20)
project(SovereignOrtRunner LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(sovereign_agent_runner SHARED "C:\WEB CASE STUDY\sonic_dna_engine\sovereign_agent_runner.cpp")

target_include_directories(sovereign_agent_runner PRIVATE "C:\WEB CASE STUDY\.venv\Lib\site-packages\onnxruntime")
target_link_directories(sovereign_agent_runner PRIVATE "C:\WEB CASE STUDY\.venv\Lib\site-packages\onnxruntime\capi")
target_link_libraries(sovereign_agent_runner PRIVATE onnxruntime)
