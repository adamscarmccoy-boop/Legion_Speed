#ifndef RAY_WORKER_HPP
#define RAY_WORKER_HPP

#include <vector>
#include <cstdint>
#include <cstring>
#include <string>
#include <algorithm>

// Standalone CUDA IPC Transfer Metadata
struct CudaIpcTransferMeta {
    uint32_t worker_id;
    size_t buffer_size_bytes;
    uint8_t handle_bytes[64]; // sizeof(cudaIpcMemHandle_t) on CUDA platforms
};

class RayCoreWorkerActor {
private:
    int worker_id_;
    int gpu_id_;
    size_t buffer_size_;
    float* d_vram_buffer_;
    std::string status_;

public:
    RayCoreWorkerActor();
    RayCoreWorkerActor(int worker_id, int gpu_id, size_t buffer_size_bytes);
    ~RayCoreWorkerActor();

    bool InitializeCore();
    std::vector<uint8_t> ExecuteTaskAndGetIpcHandle(const std::vector<float>& action_vector);
    std::string GetStatus() const;
};

#endif // RAY_WORKER_HPP
