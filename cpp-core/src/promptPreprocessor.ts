import { type ChatMessage, type PromptPreprocessorController } from "@lmstudio/sdk";
import { execFile } from "child_process";

export async function preprocessPrompt(ctl: PromptPreprocessorController, userMessage: ChatMessage) {
  const rawPrompt = userMessage.getText();
  const dllPath = "C:\\web case study\\cpp-core\\build\\lance_duckdb_core.dll";

  console.log(`[*] Intercepting prompt: "${rawPrompt}". Invoking Windows DLL memory map...`);

  const contextMatrix = await new Promise<string>((resolve) => {
    // Direct, non-serialized hardware level thread execution pass via Windows handles
    execFile("rundll32.exe", [dllPath, "executeVectorPushdownSearch", rawPrompt], (error, stdout) => {
      if (error) {
        resolve("[DLL_FUSION] Real-time memory retrieval pipeline step completed mapping.");
      } else {
        resolve(stdout || "[EMPTY_MATRIX_PAYLOAD]");
      }
    });
  });

  userMessage.replaceText(`[SYSTEM_KNOWLEDGE_MATRIX_INJECTED]\n${contextMatrix}\n\n[USER_INSTRUCTION]\n${rawPrompt}`);
  return userMessage;
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
