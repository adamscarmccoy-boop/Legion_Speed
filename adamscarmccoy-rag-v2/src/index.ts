import { type PluginContext } from "@lmstudio/sdk";
import { configSchematics } from "./config";
import { preprocess } from "./promptPreprocessor";

// This is the entry point of the plugin. The main function is to register different components of
// the plugin, such as promptPreprocessor, predictionLoopHandler, etc.
//
// You do not need to modify this file unless you want to add more components to the plugin, and/or
// add custom initialization logic.

export async function main(context: PluginContext) {
  // Register the configuration schematics.
  context.withConfigSchematics(configSchematics);
  // Register the promptPreprocessor.
  context.withPromptPreprocessor(preprocess);
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
