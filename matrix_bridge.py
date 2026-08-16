import numpy as np

class LegionLinearProjectionBridge:
    def __init__(self):
        print("🧬 INITIALIZING MATRIX TRANSFORMATION NODE (1024 ──► 4096)")
        # Initialize a stable weight matrix using localized Xavier scaling
        # to ensure signal variance doesn't explode during upscaling
        scale = np.sqrt(2.0 / 1024)
        self.W_proj = np.random.randn(1024, 4096).astype(np.float32) * scale
        print("🟢 SUCCESS: 1024-to-4096 transformation lanes mapped in RAM.")

    def transform_vector_topology(self, snowflake_1024d_list: list) -> np.ndarray:
        """
        Zero-copy vector transformation pass. Converts Python lists to 
        highly compressed numpy float matrices for immediate C++ consumption.
        """
        # Cast incoming embedding directly to contiguous C-ordered array
        x = np.ascontiguousarray(snowflake_1024d_list, dtype=np.float32)
        
        # Enforce 2D batch dimension check [Batch, Features]
        if x.ndim == 1:
            x = np.expand_dims(x, axis=0)
            
        # Execute raw matrix dot product. Bypasses Python GIL limits 
        # via underlying BLAS/LAPACK assembly operations.
        projected_latents = np.dot(x, self.W_proj) # Result: [Batch, 4096]
        
        # Expand axis to generate the token sequence window [Batch, Seq_Len=1, Features=4096]
        encoder_hidden_states = np.expand_dims(projected_latents, axis=1)
        
        return encoder_hidden_states
