import ray
import sys
import onnxruntime as rt
import numpy as np

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


sys.stdout.reconfigure(encoding='utf-8')

print("Connecting to Ray Swarm...")
ray.init(namespace="legion", ignore_reinit_error=True)

try:
    registry = ray.get_actor("CodeSwarmKnowledgeRegistry", namespace="legion")
except Exception as e:
    print("Could not find SwarmKnowledgeRegistry actor. Make sure the swarm is running.")
    sys.exit(1)

print("Fetching Swarm tables...")
# The actor has a method get_registered_tables_summary()
summary = ray.get(registry.get_registered_tables_summary.remote())

print("\nLoading Code Genome Brain ONNX model...")
sess = rt.InferenceSession(r"C:\WEB CASE STUDY\mastered_output\code_genome_brain.onnx")
input_name = sess.get_inputs()[0].name
label_name = sess.get_outputs()[0].name

print("\n========================================================")
print("  🧠 CODE GENOME BRAIN: REAL DATA CLASSIFICATION RESULTS ")
print("========================================================")

mean = np.array([2000.0, 50.0])
std = np.array([5000.0, 200.0])

count = 0
for table_name, stats in summary.items():
    if count >= 15:
        break
    
    rows = stats.get('rows', 0)
    # size isn't easily available in the summary, let's fake size for the demo based on rows just to show inference works, or just query the actual table
    table = ray.get(registry.query_table.remote(table_name))
    if not table:
        continue
        
    size_kb = table.nbytes / 1024.0
    
    # Scale input and CAST TO FLOAT32 to avoid the double crash
    raw_input = np.array([[size_kb, rows]], dtype=np.float32)
    scaled_input = ((raw_input - mean) / std).astype(np.float32)
    
    try:
        pred = sess.run([label_name], {input_name: scaled_input})
        pred_idx = int(pred[0][0])
        categories = ["aif", "aiff", "flac", "json", "m4a", "mp3", "wav"]
        predicted_category = categories[pred_idx] if pred_idx < len(categories) else "unknown"
        
        print(f"📄 {table_name[:40].ljust(40)} | Size: {size_kb:8.2f} KB | Rows: {rows:5d} => 🧬 PREDICTION: [{predicted_category.upper()}]")
        count += 1
    except Exception as e:
        print(f"Failed on {table_name}: {e}")

print("========================================================")