import { lmstudioMemoryEmbeddingProviderAdapter as MemoryEmbeddingProviderAdapter } from "@lmstudio/sdk";
//#region extensions/lmstudio/memory-embedding-adapter.d.ts
declare const lmstudioMemoryEmbeddingProviderAdapter: MemoryEmbeddingProviderAdapter;
//#endregion
export { lmstudioMemoryEmbeddingProviderAdapter };
import { lmstudioMemoryEmbeddingProviderAdapter as MemoryEmbeddingProviderAdapter } from "@lmstudio/sdk";
//#region extensions/lmstudio/memory-embedding-adapter.d.ts
declare const lmstudioMemoryEmbeddingProviderAdapter: MemoryEmbeddingProviderAdapter;
//#endregion
export { lmstudioMemoryEmbeddingProviderAdapter };

// ==============================================================================
// SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
// Prevents "ClientHolder finalized without dropping" socket leaks in LM Studio
// ==============================================================================
if (typeof process !== 'undefined') {
  const gracefulShutdown = async (signal) => {
    console.warn(`\n[LMS LIFECYCLE] Intercepted signal ${signal}. Cleanly dropping LM Studio connections...`);
    try {
      if (typeof client !== 'undefined' && client && typeof client.close === 'function') {
        await client.close();
        console.log("[LMS LIFECYCLE] Connection closed successfully.");
      }
    } catch (err) {
      console.error("[LMS LIFECYCLE] Error during connection drop:", err);
    }
    process.exit(0);
  };
  process.on("SIGINT", () => gracefulShutdown("SIGINT"));
  process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
}
// ==============================================================================
