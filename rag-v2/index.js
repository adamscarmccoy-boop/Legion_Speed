// C:\WEB CASE STUDY\rag-v2\index-v2.js
const { LMStudioClient } = require("@lmstudio/sdk");
const { spawn } = require("child_process");
const net = require("net");
const fs = require("fs");

const CONFIG = {
    LM_STUDIO_URL: "ws://127.0.0.1:1234",
    PIPE_NAME: "\\\\.\\pipe\\RAGv1",
    EXE_PATH: "C:\\WEB CASE STUDY\\legion_brain.exe" // Compile main.cpp to this location
};

let cppProcess = null;

/**
 * Automatically boots the high-performance C++ backend.
 */
function spawnCppBackend() {
    if (!fs.existsSync(CONFIG.EXE_PATH)) {
        console.warn("⚠️ [JS HOST] Compiled C++ binary not found at " + CONFIG.EXE_PATH);
        console.warn("   Run MSVC or your build system first to compile main.cpp.");
        return;
    }

    console.log(`🚀 [JS HOST] Spawning Bare-Metal C++ Core: ${CONFIG.EXE_PATH}`);
    try {
        cppProcess = spawn(CONFIG.EXE_PATH, [], {
            detached: true,
            stdio: "inherit" // Forwards std::cout logs directly to your active PowerShell
        });

        cppProcess.unref(); // Detach handle so JS parent can exit cleanly

        cppProcess.on("error", (err) => {
            console.error("❌ [JS HOST] Failed to spawn C++ child process:", err.message);
        });
    } catch (err) {
        console.error("❌ [JS HOST] Exception while spawning C++ process:", err.message);
    }
}

/**
 * Transports prompt data over Windows Named Pipe in microseconds (0ms network tax).
 */
function queryCppNamedPipe(prompt) {
    return new Promise((resolve) => {
        const client = net.createConnection(CONFIG.PIPE_NAME, () => {
            // Direct raw byte write with a null-terminator for standard C-string parsing
            client.write(prompt + "\0");
        });

        let responseBuffer = "";

        client.on("data", (data) => {
            responseBuffer += data.toString();
            if (responseBuffer.includes("\0") || responseBuffer.length > 0) {
                client.end();
            }
        });

        client.on("end", () => {
            const cleaned = responseBuffer.replace(/\0/g, "").trim();
            resolve(cleaned);
        });

        client.on("error", (err) => {
            console.error("❌ [IPC CONNECT ERROR] Named Pipe offline:", err.message);
            resolve(null); // Fallback gracefully to raw LLM prompt
        });
    });
}

async function main() {
    console.log("===============================================================================");
    console.log("⚡ INITIATING UNIFIED JAVASCRIPT IN-PROCESS PREPROCESSOR WITH NATIVE C++ RUNTIME");
    console.log("===============================================================================");

    // 1. Instantly spin up your C++ brain
    spawnCppBackend();

    try {
        const client = new LMStudioClient({ baseUrl: CONFIG.LM_STUDIO_URL });

        // 2. Register standard preprocessor hooks inside LM Studio
        await client.setPromptPreprocessor(async (prompt) => {
            console.log(`\n📬 [PREPROCESSOR] Intercepting user query: "${prompt.substring(0, 60)}..."`);

            const cppContext = await queryCppNamedPipe(prompt);

            if (cppContext) {
                console.log("✅ [PREPROCESSOR] Integrated Bare-Metal C++ Context successfully.");
                return `[System Context: ${cppContext}]\n\n${prompt}`;
            }

            console.warn("⚠️ [PREPROCESSOR] C++ Pipe timed out or offline. Bypassing context injection.");
            return prompt;
        });

        // 3. Graceful lifecycle shutdown to prevent Windows zombie threads
        const gracefulShutdown = async (signal) => {
            console.warn(`\n[LMS LIFECYCLE] Signal ${signal} intercepted.`);
            if (cppProcess && !cppProcess.killed) {
                console.log("[LMS LIFECYCLE] Purging background C++ process group...");
                try {
                    process.kill(-cppProcess.pid);
                } catch (e) {
                    // Fallback if process group mapping is not supported
                    cppProcess.kill();
                }
            }
            if (client) await client.close();
            process.exit(0);
        };

        process.on("SIGINT", () => gracefulShutdown("SIGINT"));
        process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));

    } catch (err) {
        console.error("❌ [FATAL] Node pipeline initialization failed:", err.message);
    }
}

main();

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
