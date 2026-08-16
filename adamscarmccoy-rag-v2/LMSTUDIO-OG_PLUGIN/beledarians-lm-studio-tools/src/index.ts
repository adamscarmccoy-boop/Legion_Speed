import { type PluginContext, LMStudioClient } from "@lmstudio/sdk";
import { toolsProvider } from "./toolsProvider";
import { promptPreprocessor } from "./promptPreprocessor";
import { pluginConfigSchematics } from "./config";

export async function main(context: PluginContext) {
  // Register the configuration schematics.
  context.withConfigSchematics(pluginConfigSchematics);

  // Register the tools provider.
  context.withToolsProvider(toolsProvider);
  
  // Register the prompt preprocessor to inject documentation on startup.
  context.withPromptPreprocessor(promptPreprocessor);
}


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
