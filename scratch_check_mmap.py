import glob, os, numpy as np

print("=== MMAP / BINARY VECTOR FILES ===")
extensions = ('.mmap', '.bin', '.npy', '.npz', '.dat', '.vec', '.index', '.faiss', '.annoy', '.hnsw')
total_vectors = 0

for f in glob.glob('**/*', recursive=True):
    if not os.path.isfile(f):
        continue
    ext = os.path.splitext(f)[1].lower()
    size = os.path.getsize(f)
    if size == 0:
        continue

    if ext == '.npy':
        try:
            arr = np.load(f, mmap_mode='r')
            print(f"[NPY]   {f}")
            print(f"        shape={arr.shape} dtype={arr.dtype} size={size/1e6:.2f}MB")
            total_vectors += arr.shape[0] if arr.ndim > 0 else 1
        except Exception as e:
            print(f"[NPY-ERR] {f}: {e}")

    elif ext == '.npz':
        try:
            d = np.load(f, allow_pickle=True)
            print(f"[NPZ]   {f} | keys={list(d.keys())} size={size/1e6:.2f}MB")
            for k in d.keys():
                arr = d[k]
                print(f"        '{k}' shape={arr.shape} dtype={arr.dtype}")
                total_vectors += arr.shape[0] if arr.ndim > 0 else 1
        except Exception as e:
            print(f"[NPZ-ERR] {f}: {e}")

    elif ext == '.mmap':
        print(f"[MMAP]  {f} | size={size/1e6:.2f}MB ({size/4:,.0f} f32 elements if float32)")

    elif ext in ('.faiss', '.index'):
        print(f"[FAISS] {f} | size={size/1e6:.2f}MB")
        try:
            import faiss
            idx = faiss.read_index(f)
            print(f"        ntotal={idx.ntotal:,} d={idx.d}")
            total_vectors += idx.ntotal
        except Exception as e:
            print(f"        (faiss not loaded: {e})")

    elif ext == '.bin':
        print(f"[BIN]   {f} | size={size/1e6:.2f}MB")

print(f"\n=== TOTAL VECTOR POINTS FROM MMAP/NPY/FAISS: {total_vectors:,} ===")
