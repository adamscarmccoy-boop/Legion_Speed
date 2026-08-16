#include <iostream>
#include <vector>
#include <string>
#include <filesystem>
#include <fstream>
#include <chrono>

namespace fs = std::filesystem;

struct NativeFileEntry {
    std::string filename;
    std::string extension;
    uintmax_t size_bytes;
    std::string full_path;
};

bool is_native_source(const std::string& ext) {
    return ext == ".cpp" || ext == ".hpp" || ext == ".h" || 
           ext == ".cu"  || ext == ".cuh" || ext == ".c" || 
           ext == ".cxx" || ext == ".pyd" || ext == ".bin";
}

bool should_skip_dir(const std::string& dir_name) {
    return dir_name == ".venv" || dir_name == ".venv_314" || 
           dir_name == "node_modules" || dir_name == ".git" || 
           dir_name == "build" || dir_name == "dist";
}

void scan_directory(const fs::path& root_path, std::vector<NativeFileEntry>& results) {
    if (!fs::exists(root_path)) return;
    
    try {
        for (const auto& entry : fs::recursive_directory_iterator(root_path, fs::directory_options::skip_permission_denied)) {
            if (entry.is_directory()) {
                if (should_skip_dir(entry.path().filename().string())) {
                    // Note: skip_permission_denied iterator continues
                }
            } else if (entry.is_regular_file()) {
                std::string ext = entry.path().extension().string();
                for (auto & c: ext) c = tolower(c);
                
                // Exclude virtualenvs
                std::string full = entry.path().string();
                if (full.find("\\.venv") != std::string::npos || full.find("\\node_modules") != std::string::npos) {
                    continue;
                }
                
                if (is_native_source(ext)) {
                    results.push_back({
                        entry.path().filename().string(),
                        ext,
                        entry.file_size(),
                        full
                    });
                }
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "[SCAN_WARNING] " << e.what() << std::endl;
    }
}

int main() {
    auto start_time = std::chrono::high_resolution_clock::now();

    std::vector<fs::path> search_roots = {
        "C:\\WEB CASE STUDY",
        "C:\\STUDIES_BACKUP\\Legion-Jacked-Pipeline"
    };

    std::vector<NativeFileEntry> native_files;
    for (const auto& root : search_roots) {
        scan_directory(root, native_files);
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    double elapsed_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();

    std::cout << "==================================================================" << std::endl;
    std::cout << "🏛️ SOVEREIGN C++ & NATIVE SOURCE MANIFEST (SCAN TIME: " << elapsed_ms << " ms)" << std::endl;
    std::cout << "==================================================================" << std::endl;
    std::cout << "Total Native Files Discovered: " << native_files.size() << std::endl << std::endl;

    for (const auto& f : native_files) {
        std::cout << "• [" << f.extension << "] " << f.filename << " (" << f.size_bytes << " bytes)" << std::endl;
        std::cout << "  Path: " << f.full_path << std::endl;
    }

    std::cout << "==================================================================" << std::endl;
    return 0;
}
