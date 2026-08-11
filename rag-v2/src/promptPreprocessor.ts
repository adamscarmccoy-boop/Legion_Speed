// This is the main plugin entry point for LM Studio.

import { LanceDBService, getLanceDBPath, CodeRoleResult, LanceDBSearchResult } from './services/LanceDBService';
import { DuckDBService } from './services/DuckDBService';
import { MontyNativeService, MontyInputs, MontyExternalLookups } from './services/MontyNativeService';
import { LMStudioRouter, LMStudioAI } from './services/LMStudioRouter';
import * as path from 'path'; // For path resolution of hardpaths
import * as fs from 'fs'; // For reading hardpaths.json

// --- Global/Configuration Constants ---
const LANCEDB_DB_PATH = getLanceDBPath(); // Dynamically determined LanceDB path
const DUCKDB_DB_PATH = "C:\\WEB CASE STUDY\\web_intel_sonicdb.duckdb"; // Real DuckDB database file
const EMBEDDING_DIMENSION = 1024; // Expected dimension for text-embedding-snowflake-arctic-embed-l-v2.0

// Define a simple Prometheus-like registry for tracing/metrics
class PrometheusRegistryStub {
    private metrics: { [key: string]: number } = {};

    public increment(key: string, value: number = 1): void {
        this.metrics[key] = (this.metrics[key] || 0) + value;
        // console.log(`Metric ${key} incremented to: ${this.metrics[key]}`); // Verbose logging
    }

    public get(key: string): number {
        return this.metrics[key] || 0;
    }

    public getAll(): { [key: string]: number } {
        return { ...this.metrics };
    }
}
const PROMETHEUS_REGISTRY = new PrometheusRegistryStub(); // Global instance

// Define interface for sovereign_hardpaths.json content
interface SovereignHardpaths {
    root_dir: string;
    [key: string]: string; // Allows for other dynamic hardpaths
}

/**
 * Loads hardcoded paths from a `sovereign_hardpaths.json` file.
 * This file is expected to be located in the plugin's root directory.
 * Provides fallback defaults if the file is not found.
 * @returns An object containing the loaded hardpaths.
 */
function loadHardpaths(): SovereignHardpaths {
    // Attempt to load from a `hardpaths.json` in the plugin's root directory.
    // `process.cwd()` often points to the LM Studio's executable directory, or the plugin's directory.
    // For robust production, hardpaths might be bundled or user-configurable.
    const hardpathsFilePath = path.join(process.cwd(), 'sovereign_hardpaths.json');
    try {
        if (fs.existsSync(hardpathsFilePath)) {
            const data = fs.readFileSync(hardpathsFilePath, 'utf8');
            console.log(`Plugin: Loaded hardpaths from: ${hardpathsFilePath}`);
            return JSON.parse(data) as SovereignHardpaths;
        } else {
            console.warn(`Plugin: Hardpaths file not found at: ${hardpathsFilePath}. Using default/empty hardpaths.`);
            return { root_dir: process.cwd() }; // Fallback
        }
    } catch (error) {
        console.error(`Plugin: Error loading hardpaths from ${hardpathsFilePath}:`, error);
        return { root_dir: process.cwd() }; // Fallback
    }
}

const HARDPATHS = loadHardpaths(); // Initialize global HARDPATHS
const SOVEREIGN_TARGET_RMS = -13.9;
const SOVEREIGN_TARGET_CREST = 5.69;
const MAX_LATENCY_THRESHOLD = 50; // milliseconds, for Monty benchmarks


// --- Service Instances ---
let lanceDBService: LanceDBService;
let duckDBService: DuckDBService;
let montyNativeService: MontyNativeService;
let lmStudioRouter: LMStudioRouter;

/**
 * This function is the primary initialization entry point for the LM Studio plugin.
 * It is called by LM Studio when the plugin is loaded.
 * It sets up all necessary services (LanceDB, DuckDB, Monty, AIStudioRouter).
 * @param ai The `LMStudioAI` object provided by LM Studio for interacting with its native features.
 */
export async function initialize(ai: LMStudioAI): Promise<void> {
    console.log("ADAMSCARMCCOY-RAG-V2 Plugin: Initializing...");

    // Initialize AIStudioRouter first, as other services might depend on it for embeddings.
    lmStudioRouter = LMStudioRouter.getInstance(EMBEDDING_DIMENSION);
    lmStudioRouter.setAIContext(ai); // Pass LM Studio's AI object to the router

    lanceDBService = new LanceDBService(LANCEDB_DB_PATH, "mined_code_vectors", EMBEDDING_DIMENSION);
    duckDBService = new DuckDBService(DUCKDB_DB_PATH);
    montyNativeService = new MontyNativeService(lanceDBService, duckDBService);

    try {
        await lanceDBService.init();
        await duckDBService.init();
        await montyNativeService.init(); // This also initializes ONNX Runtime

        // OPTIONAL: Load some dummy data into DuckDB for structured search testing
        // In a real scenario, this data would come from an ingestion pipeline.
        const dummyCodeMetadata: CodeRoleResult[] = [
            { id: "func_1", role_type: "function", filepath: "src/utils/math.ts", symbol_name: "add", line_start: 1, line_end: 5, code_content: "function add(a: number, b: number) { return a + b; }" },
            { id: "class_A", role_type: "class", filepath: "src/core/model.ts", symbol_name: "Model", line_start: 10, line_end: 20, code_content: "class Model { constructor() {} }" },
            { id: "func_2", role_type: "function", filepath: "src/utils/string.ts", symbol_name: "capitalize", line_start: 1, line_end: 7, code_content: "function capitalize(s: string) { return s.charAt(0).toUpperCase() + s.slice(1); }" },
            { id: "func_3", role_type: "function", filepath: "src/utils/security.ts", symbol_name: "deleteFile", line_start: 1, line_end: 5, code_content: "function deleteFile(path: string) { /* unsafe operation */ os.remove(path); }" } // Unsafe example
        ];
        // Uncomment the line below to load dummy data into DuckDB for testing structured searches.
        // await duckDBService.loadCodeMetadata(dummyCodeMetadata);

        console.log("ADAMSCARMCCOY-RAG-V2 Plugin: All services initialized successfully.");
    } catch (error) {
        console.error("ADAMSCARMCCOY-RAG-V2 Plugin: Failed to initialize one or more services:", error);
        // Important: If initialization fails, throw the error to prevent the plugin from loading partially.
        throw error;
    }
}

/**
 * This is the core plugin function, called by LM Studio every time a user prompt is processed.
 * It performs RAG, Monty verification, and ONNX code genome verification to augment the prompt.
 * @param prompt The original user's prompt text.
 * @returns A Promise resolving to an array of strings that will be prepended to the user's prompt.
 */
export async function preprocess(ctl: any, userMessage: any): Promise<any> {
    const prompt = userMessage.getText();
    console.log(`ADAMSCARMCCOY-RAG-V2 Plugin: Processing prompt: "${prompt.substring(0, 100)}..."`);
    const augmentedContext: string[] = [];
    PROMETHEUS_REGISTRY.increment('prompt_process_total');

    // 1. Initial RAG search (semantic + structured) based on the prompt
    const k_semantic = 5; // Number of semantic results to retrieve
    const k_structured = 5; // Number of structured results to retrieve

    let semanticResults: LanceDBSearchResult[] = [];
    let structuredResults: CodeRoleResult[] = [];

    try {
        // Perform semantic search using LanceDB
        semanticResults = await lanceDBService.semanticCodeSearch(prompt, k_semantic);
        PROMETHEUS_REGISTRY.increment('lancedb_search_total');

        // Perform structured search using DuckDB
        // This is a simplistic example; a real one would parse the prompt for keywords
        // or use more sophisticated SQL based on recognized entities.
        const keywords = prompt.split(/\s+/)
                               .filter(w => w.length > 2 && !['the', 'and', 'for', 'with'].includes(w.toLowerCase()))
                               .map(w => `%${w}%`); // Add wildcards for LIKE matching

        if (keywords.length > 0) {
            // Construct a SQL query to search in symbol_name or code_content
            const sqlConditions = keywords.map(kw => `symbol_name ILIKE '${kw}' OR code_content ILIKE '${kw}'`).join(' OR ');
            const sqlQuery = `SELECT * FROM code_metadata WHERE ${sqlConditions} LIMIT ${k_structured};`;
            structuredResults = await duckDBService.duckdbCodeSearch<CodeRoleResult>(sqlQuery);
            PROMETHEUS_REGISTRY.increment('duckdb_search_total');
        }

        console.log(`RAG: Found ${semanticResults.length} semantic and ${structuredResults.length} structured code blocks.`);
    } catch (error) {
        console.error("Error during initial RAG search:", error);
        PROMETHEUS_REGISTRY.increment('rag_search_failures_total');
    }

    // Combine results from both search types, ensuring unique IDs if possible
    const candidateASTsMap = new Map<string, CodeRoleResult>();
    semanticResults.forEach(r => candidateASTsMap.set(r.id, { ...r, provenance: "semantic" }));
    structuredResults.forEach(r => candidateASTsMap.set(r.id, { ...r, provenance: "structured" })); // Structured results might override semantic if IDs collide

    const candidateASTs: CodeRoleResult[] = Array.from(candidateASTsMap.values());

    const verifiedContextBlocks: string[] = [];
    let montyRejectedCount = 0;
    let onnxRejectedCount = 0;

    // 2. Monty Native Sandbox Verification
    // Iterate through all candidate ASTs and verify them using Monty.
    for (const astBlock of candidateASTs) {
        const montySession = montyNativeService.createSession().checkout(); // Checkout a new session for each block

        // Prepare inputs for Monty (global variables/configuration)
        const nativeInputs: MontyInputs = {
            "HARDPATHS": HARDPATHS,
            "SOVEREIGN_TARGET_RMS": SOVEREIGN_TARGET_RMS,
            "SOVEREIGN_TARGET_CREST": SOVEREIGN_TARGET_CREST,
            "PROMETHEUS_REGISTRY": PROMETHEUS_REGISTRY, // Pass the registry directly for internal metric updates
            "MAX_LATENCY_THRESHOLD": MAX_LATENCY_THRESHOLD,
        };

        // Prepare external lookups for Monty (lazy host functions)
        const nativeLookups: MontyExternalLookups = {
            "semantic_code_search_native": (query: string, k: number = 3) => lanceDBService.semanticCodeSearch(query, k),
            "duckdb_code_search_native": (sql: string) => duckDBService.duckdbCodeSearch<any>(sql),
            // "swarm_code_search_native": async (query: string) => { /* Placeholder for Ray FFI */ return []; }
        };

        try {
            const montyStartTime = Date.now();
            const isVerified = await montySession.feedRun(astBlock.code_content, nativeInputs, nativeLookups);
            const montyLatency = Date.now() - montyStartTime;

            PROMETHEUS_REGISTRY.increment('monty_runs_successful');
            // PROMETHEUS_REGISTRY.observe('monty_run_latency_ms', montyLatency); // If PrometheusRegistryStub had an observe method

            if (isVerified) {
                console.log(`Monty verified AST block (ID: ${astBlock.id}, Latency: ${montyLatency}ms).`);
                PROMETHEUS_REGISTRY.increment('monty_verified_total');

                // 3. Native ONNX Code Genome Verification (post-Monty safety check)
                // Simulate Omni-Vector generation: 768-D embed + 2-D footprint.
                // The LM Studio AI router generates the 768-D part.
                const embeddingVector: number[] = await aiStudioRouter.generateEmbedding(astBlock.code_content);
                // Add dummy 2-D footprint (e.g., lines of code, cyclomatic complexity)
                const omniVector = [...embeddingVector];
                omniVector.push(astBlock.code_content.split('\n').length); // Line count as a feature
                omniVector.push(Math.floor(Math.random() * 10) + 1); // Dummy complexity score (1-10)

                const onnxResult = await montyNativeService.performOnnxVerification(omniVector);

                if (onnxResult.verified) {
                    // If both Monty and ONNX verify, add to the context.
                    verifiedContextBlocks.push(`\`\`\`${astBlock.filepath}\n${astBlock.code_content}\n\`\`\``);
                    PROMETHEUS_REGISTRY.increment('onnx_verified_total');
                } else {
                    console.warn(`ONNX rejected AST block (ID: ${astBlock.id}, Score: ${onnxResult.score}).`);
                    onnxRejectedCount++;
                    PROMETHEUS_REGISTRY.increment('onnx_rejections_total');
                }
            } else {
                // This branch should ideally not be hit if feedRun throws on rejection,
                // but included for completeness if feedRun returns false.
                console.warn(`Monty did not verify AST block (ID: ${astBlock.id}).`);
                montyRejectedCount++;
                PROMETHEUS_REGISTRY.increment('monty_rejections_total');
            }
        } catch (e: any) {
            console.warn(`Monty evaluation failed for AST block (ID: ${astBlock.id}): ${e.message}`);
            montyRejectedCount++;
            PROMETHEUS_REGISTRY.increment('monty_failures_total');
        }
    }

    // Prepare the final augmented context string for the LLM
    if (verifiedContextBlocks.length > 0) {
        augmentedContext.push("\n<RAG_CONTEXT_START>\n");
        augmentedContext.push("The following code snippets are relevant to your query and have passed all verification checks:\n\n");
        augmentedContext.push(...verifiedContextBlocks);
        augmentedContext.push("\n<RAG_CONTEXT_END>\n");
    } else {
        augmentedContext.push("\n<RAG_CONTEXT_START>\n");
        augmentedContext.push("No relevant or verified code context found for your query. Proceeding with general knowledge.\n");
        augmentedContext.push("\n<RAG_CONTEXT_END>\n");
    }

    console.log(`ADAMSCARMCCOY-RAG-V2 Pipeline Summary: ${verifiedContextBlocks.length} blocks verified, ${montyRejectedCount} Monty rejected, ${onnxRejectedCount} ONNX rejected.`);
    console.log("Current Prometheus Metrics:", PROMETHEUS_REGISTRY.getAll());

    return augmentedContext;
}

/**
 * This optional function is called by LM Studio when the plugin is unloaded.
 * It's crucial for releasing resources and performing graceful shutdowns.
 */
export async function shutdown(): Promise<void> {
    console.log("ADAMSCARMCCOY-RAG-V2 Plugin: Shutting down services...");
    PROMETHEUS_REGISTRY.increment('plugin_shutdown_total');
    try {
        await lanceDBService.disconnect();
        await duckDBService.disconnect();
        await montyNativeService.disconnect();
        console.log("ADAMSCARMCCOY-RAG-V2 Plugin: All services disconnected.");
    } catch (error) {
        console.error("ADAMSCARMCCOY-RAG-V2 Plugin: Error during shutdown:", error);
    }
}