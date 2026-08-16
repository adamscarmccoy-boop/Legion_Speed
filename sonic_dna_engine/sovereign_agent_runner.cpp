#include "SovereignOrtBinding.h" // Includes the class defined above
#include <array>
#include <iostream>

int main() {
  // 1. Initialize once outside the audio thread (e.g. host setup /
  // prepareToPlay)
  std::unique_ptr<SovereignOrtBinding> engine;
  try {
    engine = std::make_unique<SovereignOrtBinding>(
        L"C:/WEB CASE STUDY/sovereign_big_brain_exhaustive.onnx");
  } catch (const std::exception &e) {
    std::cerr << "[CRITICAL] Engine initialization failed: " << e.what()
              << std::endl;
    return 1;
  }

  // 2. Pre-allocated buffers matching real-time constraints
  std::array<float, 64> state_tensor{};
  std::array<float, 12> dsp_state{};

  // Populate control slots (Slot 0: Opcode, Slot 1: Task Type, Slot 8: RMS dB,
  // Slot 11: Mono 150Hz Energy, etc.)
  state_tensor[0] = 1.0f;   // Opcode: RUN_INFERENCE
  state_tensor[1] = 2.0f;   // Task Type: CODE_GEN_ROUTER
  state_tensor[8] = -14.0f; // Input RMS dB
  state_tensor[11] = 0.95f; // 150Hz Mono Truth active

  // 3. Zero-allocation execution inside processBlock audio thread callback
  if (engine && engine->process_block(state_tensor, dsp_state)) {
    std::cout << "[SUCCESS] ORT Inference complete. DSP Output Parameter 0: "
              << dsp_state[0] << std::endl;
  } else {
    std::cerr
        << "[WARNING] Audio block processing bypassed due to inference failure."
        << std::endl;
  }

  return 0;
}