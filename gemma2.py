import os
import sys

MODEL_DIR = r"C:\WEB CASE STUDY\gemma_onnx"

REQUIRED_FILES = [
    "model.onnx",
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
]

print("=" * 60)
print("GEMMA ONNX VERIFICATION")
print("=" * 60)

# --------------------------------------------------
# Check files
# --------------------------------------------------

missing = []

for file in REQUIRED_FILES:
    path = os.path.join(MODEL_DIR, file)

    if not os.path.exists(path):
        missing.append(file)

if missing:
    print("\nMissing required files:")
    for f in missing:
        print(" -", f)

    sys.exit(1)

print("Required files found.")

# --------------------------------------------------
# Verify ONNX
# --------------------------------------------------

try:
    import onnx

    print("\nLoading ONNX model...")

    model_path = os.path.join(MODEL_DIR, "model.onnx")

    model = onnx.load(model_path)

    try:
        onnx.checker.check_model(model)
        print("ONNX validation passed.")
    except Exception as e:
        print("ONNX checker warning:")
        print(e)

except Exception as e:
    print("\nFailed loading ONNX:")
    print(e)
    sys.exit(1)

# --------------------------------------------------
# Verify ONNX Runtime
# --------------------------------------------------

try:
    import onnxruntime as ort

    print("\nCreating ONNX Runtime session...")

    session = ort.InferenceSession(
        model_path,
        providers=["CPUExecutionProvider"]
    )

    print("Session created successfully.")

    print("\nInputs:")
    for i in session.get_inputs():
        print(
            f"  {i.name} | "
            f"Shape={i.shape} | "
            f"Type={i.type}"
        )

    print("\nOutputs:")
    for o in session.get_outputs():
        print(
            f"  {o.name} | "
            f"Shape={o.shape} | "
            f"Type={o.type}"
        )

except Exception as e:
    print("\nONNX Runtime failed:")
    print(e)
    sys.exit(1)

# --------------------------------------------------
# Generative AI test
# --------------------------------------------------

try:
    import onnxruntime_genai as og

    print("\nTesting text generation...")

    model = og.Model(MODEL_DIR)

    tokenizer = og.Tokenizer(model)

    prompt = "What is artificial intelligence?"

    tokens = tokenizer.encode(prompt)

    params = og.GeneratorParams(model)

    try:
        params.set_search_options(
            max_length=100
        )
    except:
        pass

    generator = og.Generator(model, params)

    generator.append_tokens(tokens)

    print("\nMODEL OUTPUT:")
    print("-" * 60)

    while not generator.is_done():

        generator.generate_next_token()

        token = generator.get_next_tokens()[0]

        text = tokenizer.decode([token])

        print(text, end="", flush=True)

    print("\n")
    print("-" * 60)
    print("Generation succeeded.")

except ModuleNotFoundError:
    print("\nonnxruntime-genai not installed.")
    print("Install with:")
    print("pip install onnxruntime-genai")

except Exception as e:
    print("\nGeneration test failed:")
    print(e)

print("\nVerification completed.")