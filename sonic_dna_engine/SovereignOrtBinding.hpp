#include <array>
#include <iostream>
#include <memory>
#include <onnxruntime_cxx_api.h>

class SovereignOrtBinding {
public:
  explicit SovereignOrtBinding(const wchar_t *model_path) {
    try {
      env_ = Ort::Env(ORT_LOGGING_LEVEL_WARNING, "SovereignCompiledEngine");
      session_options_.SetIntraOpNumThreads(
          1); // Lock to single thread for audio thread isolation
      session_options_.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
      session_ = std::make_unique<Ort::Session>(env_, model_path, session_options_);
      memory_info_ = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
    } catch (const Ort::Exception &e) {
      std::cerr << "[SOVEREIGN_ORT_INIT_FAILED] " << e.what() << std::endl;
      throw;
    }
  }

  // Zero-allocation call inside C++ Pedalboard processBlock
  bool process_block(const std::array<float, 64> &state_tensor_in,
                     std::array<float, 12> &dsp_state_out) noexcept {
    try {
      constexpr int64_t input_shape[] = {1, 64};
      constexpr int64_t output_shape[] = {1, 12};

      Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
          memory_info_, const_cast<float *>(state_tensor_in.data()),
          state_tensor_in.size(), input_shape, 2);

      Ort::Value output_tensor = Ort::Value::CreateTensor<float>(
          memory_info_, dsp_state_out.data(), dsp_state_out.size(),
          output_shape, 2);

      const char *input_names[] = {"state_tensor"};
      const char *output_names[] = {"dsp_state"};

      session_->Run(Ort::RunOptions{nullptr}, input_names, &input_tensor, 1,
                    output_names, &output_tensor, 1);
      return true;
    } catch (const Ort::Exception &) {
      // Non-allocating fallback to protect real-time audio thread
      return false;
    }
  }

private:
  Ort::Env env_{nullptr};
  Ort::SessionOptions session_options_;
  std::unique_ptr<Ort::Session> session_;
  Ort::MemoryInfo memory_info_{nullptr};
};
