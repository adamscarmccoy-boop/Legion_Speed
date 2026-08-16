import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass
import onnxruntime as rt
import numpy as np

# We take the perfectly generated hallucinated footprint from the PyTorch Autoencoder:
# Scaled Mutated Tensor: [0.44047785, 0.69666743]
synthetic_footprint = np.array([[0.44047785, 0.69666743]], dtype=np.float32)

print(f"Loading ONNX Genome Engine from C++ Binary...")
sess = rt.InferenceSession(r"C:\WEB CASE STUDY\mastered_output\code_genome_brain.onnx")

input_name = sess.get_inputs()[0].name
label_name = sess.get_outputs()[0].name
prob_name = sess.get_outputs()[1].name

print(f"Running Millisecond Inference on Synthetic Footprint: {synthetic_footprint[0]}")
# Fire the ONNX engine
pred_onx = sess.run([label_name, prob_name], {input_name: synthetic_footprint})

predicted_category = pred_onx[0][0]
probabilities = pred_onx[1][0]

print("\n🌲 ONNX GENOME INFERENCE RESULTS 🌲")
print("====================================")
print(f"The ONNX C++ Engine instantly classified this 4.4MB synthetic file as:")
print(f"-> {predicted_category.upper()}")

print("\n📊 Raw Probability Tensor:")
for cat, prob in probabilities.items():
    if prob > 0.01: # Only show likely matches
        print(f"   {cat:10}: {prob*100:.2f}%")
