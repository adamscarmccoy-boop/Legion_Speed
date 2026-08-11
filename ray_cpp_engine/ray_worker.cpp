#include "ray_worker.hpp"
#include <torch/extension.h>

#ifdef __CUDACC__
#include <cuda_runtime.h>
#endif

RayCoreWorkerActor::RayCoreWorkerActor()
    : worker_id_(0), gpu_id_(0), buffer_size_(1024 * sizeof(float)), d_vram_buffer_(nullptr), status_("UNINITIALIZED") {}

RayCoreWorkerActor::RayCoreWorkerActor(int worker_id, int gpu_id, size_t buffer_size_bytes)
    : worker_id_(worker_id), gpu_id_(gpu_id), buffer_size_(buffer_size_bytes), d_vram_buffer_(nullptr), status_("INSTANTIATED") {}

RayCoreWorkerActor::~RayCoreWorkerActor() {
#ifdef __CUDACC__
    if (d_vram_buffer_) {
        cudaFree(d_vram_buffer_);
        d_vram_buffer_ = nullptr;
    }
#else
    if (d_vram_buffer_) {
        free(d_vram_buffer_);
        d_vram_buffer_ = nullptr;
    }
#endif
}

bool RayCoreWorkerActor::InitializeCore() {
#ifdef __CUDACC__
    cudaError_t err = cudaSetDevice(gpu_id_);
    if (err != cudaSuccess) {
        status_ = "ERROR_CUDA_SET_DEVICE";
        return false;
    }
    err = cudaMalloc((void**)&d_vram_buffer_, buffer_size_);
    if (err != cudaSuccess) {
        status_ = "ERROR_CUDA_MALLOC";
        return false;
    }
    cudaMemset(d_vram_buffer_, 0, buffer_size_);
    status_ = "INITIALIZED_CUDA_VRAM";
#else
    d_vram_buffer_ = (float*)malloc(buffer_size_);
    if (d_vram_buffer_) {
        std::memset(d_vram_buffer_, 0, buffer_size_);
        status_ = "INITIALIZED_HOST_RAM";
    } else {
        status_ = "ERROR_HOST_MALLOC";
        return false;
    }
#endif
    return true;
}

std::vector<uint8_t> RayCoreWorkerActor::ExecuteTaskAndGetIpcHandle(const std::vector<float>& action_vector) {
    CudaIpcTransferMeta meta = {};
    meta.worker_id = worker_id_;
    meta.buffer_size_bytes = buffer_size_;

#ifdef __CUDACC__
    cudaSetDevice(gpu_id_);
    if (!action_vector.empty() && d_vram_buffer_) {
        size_t copy_bytes = std::min(action_vector.size() * sizeof(float), buffer_size_);
        cudaMemcpy(d_vram_buffer_, action_vector.data(), copy_bytes, cudaMemcpyHostToDevice);
    }
    cudaIpcMemHandle_t ipc_handle;
    if (d_vram_buffer_) {
        cudaIpcGetMemHandle(&ipc_handle, d_vram_buffer_);
        std::memcpy(meta.handle_bytes, &ipc_handle, sizeof(cudaIpcMemHandle_t));
    }
#else
    if (!action_vector.empty() && d_vram_buffer_) {
        size_t copy_bytes = std::min(action_vector.size() * sizeof(float), buffer_size_);
        std::memcpy(d_vram_buffer_, action_vector.data(), copy_bytes);
    }
    // Simulation handle for host / CPU fallback
    std::memset(meta.handle_bytes, 0xAA, sizeof(meta.handle_bytes));
#endif

    std::vector<uint8_t> payload(sizeof(CudaIpcTransferMeta));
    std::memcpy(payload.data(), &meta, sizeof(CudaIpcTransferMeta));
    return payload;
}

std::string RayCoreWorkerActor::GetStatus() const {
    return status_;
}

// -------------------------------------------------------------
// PYBIND11 MODULE BINDING (For PyTorch JIT cpp_extension.load)
// -------------------------------------------------------------
PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    pybind11::class_<RayCoreWorkerActor>(m, "RayCoreWorkerActor")
        .def(pybind11::init<>())
        .def(pybind11::init<int, int, size_t>(), pybind11::arg("worker_id"), pybind11::arg("gpu_id"), pybind11::arg("buffer_size_bytes"))
        .def("initialize_core", &RayCoreWorkerActor::InitializeCore)
        .def("execute_task_and_get_ipc_handle", &RayCoreWorkerActor::ExecuteTaskAndGetIpcHandle, pybind11::arg("action_vector"))
        .def("get_status", &RayCoreWorkerActor::GetStatus);
}
