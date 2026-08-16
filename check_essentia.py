import sys

# Force UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

print("=== Checking Essentia Package Installation ===")

try:
    import essentia
    import essentia.standard as es
    print("✅ Essentia imported successfully!")
    print(f"Essentia Version: {essentia.__version__}")
except ImportError as e:
    print("❌ Essentia package is NOT installed in this virtual environment.")
    print(f"Error: {e}")
