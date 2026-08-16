import { createConfigSchematics } from "@lmstudio/sdk";

export const configSchematics = createConfigSchematics()
  .field(
    "enableMcpRag",
    "boolean",
    {
      displayName: "Enable MCP RAG",
      description: "Inject Swarm Intelligence via MCP Server before the LLM processes the prompt.",
    },
    true,
  )
  .field(
    "retrievalLimit",
    "numeric",
    {
      int: true,
      min: 1,
      displayName: "Retrieval Limit",
      subtitle: "Maximum number of chunks to return for both local documents and MCP RAG.",
      slider: { min: 1, max: 10, step: 1 },
    },
    3,
  )
  .field(
    "retrievalAffinityThreshold",
    "numeric",
    {
      min: 0.0,
      max: 1.0,
      displayName: "Retrieval Affinity Threshold",
      subtitle: "The minimum similarity score for a local document chunk.",
      slider: { min: 0.0, max: 1.0, step: 0.01 },
    },
    0.5,
  )
  .field(
    "embeddingModel",
    "string",
    {
      displayName: "Embedding Model",
      subtitle: "Model to use for RAG features (default: nomic-ai/nomic-embed-text-v1.5-GGUF)",
    },
    "nomic-ai/nomic-embed-text-v1.5-GGUF"
  )
  .build();


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
