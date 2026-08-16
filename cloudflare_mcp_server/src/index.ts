import { Agent } from "agents";
import { generateText } from "ai";
import { createWorkersAI } from "workers-ai-provider";
import { z } from "zod";
// @ts-ignore
import htmlContent from "../public/index.html";

export interface Env {
  AI: any;
  LOCAL_API_URL: string;
  LOCAL_API_TOKEN?: string;
  LOCAL_RAG_URL?: string;
  LOCAL_SERVE_URL?: string;
}

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

export class LegionSwarmAgent extends Agent<Env> {
  async onStart() {
    console.log("[AGENT START] Initializing Legion Swarm Agent on Cloudflare Edge...");
  }
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const url = new URL(request.url);
    const baseUrl = env.LOCAL_API_URL;
    const ragUrl = env.LOCAL_RAG_URL;
    const serveUrl = env.LOCAL_SERVE_URL;

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    // Serve HTML Frontend
    if (url.pathname === "/") {
      return new Response(htmlContent, {
        headers: { "Content-Type": "text/html; charset=utf-8", ...CORS_HEADERS }
      });
    }

    // Health check
    if (url.pathname === "/health") {
      return Response.json({
        status: "ONLINE",
        agent: "LegionSwarmAgent",
        edge_runtime: "Cloudflare Workers",
        local_api_target: baseUrl,
        rag_target: ragUrl,
        serve_target: serveUrl,
      }, { headers: CORS_HEADERS });
    }

    // Direct proxy to local API
    if (url.pathname.startsWith("/api/proxy")) {
      const localPath = url.pathname.replace("/api/proxy", "") || "/";
      const targetUrl = `${baseUrl}${localPath}`;
      try {
        const proxyRes = await fetch(targetUrl, {
          method: request.method,
          headers: { "Content-Type": "application/json" },
          ...(request.method !== "GET" ? { body: await request.text() } : {}),
        });
        const data = await proxyRes.text();
        return new Response(data, {
          status: proxyRes.status,
          headers: { "Content-Type": "application/json", ...CORS_HEADERS }
        });
      } catch (err: any) {
        return Response.json(
          { status: "error", message: `Proxy fetch failed: ${err.message}` },
          { status: 502, headers: CORS_HEADERS }
        );
      }
    }

    // AI Generation & Full Tool Gateway
    if (url.pathname === "/api/chat" && request.method === "POST") {
      const body = (await request.json()) as { prompt: string };
      const prompt = body.prompt || "Check status of Legion Swarm";

      const workersai = createWorkersAI({ binding: env.AI });

      try {
        const response = await generateText({
          model: workersai("@cf/meta/llama-3.2-3b-instruct"),
          maxSteps: 5,
          prompt,
          tools: {
            // ── System & Brain ─────────────────────────────────────
            getSystemStatus: {
              description: "Get Legion world state from /system/status (Ray actors, services, heartbeats)",
              parameters: z.object({}),
              execute: async () => {
                const res = await fetch(`${baseUrl}/system/status`);
                return await res.text();
              },
            },
            getBrainStatus: {
              description: "Check if the AI reasoning brain (api_server_v4) is running on port 8010",
              parameters: z.object({}),
              execute: async () => {
                const res = await fetch(`${baseUrl}/brain/status`);
                return await res.text();
              },
            },
            startBrain: {
              description: "Start the AI reasoning brain subprocess (api_server_v4 on port 8010)",
              parameters: z.object({}),
              execute: async () => {
                const res = await fetch(`${baseUrl}/brain/start`, { method: "POST" });
                return await res.text();
              },
            },
            chatWithBrain: {
              description: "Send a prompt to the AI reasoning brain for deep inference",
              parameters: z.object({
                message: z.string().describe("The prompt to send to the brain"),
              }),
              execute: async ({ message }) => {
                const res = await fetch(`${baseUrl}/brain/chat`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ message }),
                });
                return await res.text();
              },
            },

            // ── Database Queries ───────────────────────────────────
            queryLanceDB: {
              description: "Query the LanceDB vector database for semantic audio/embedding search",
              parameters: z.object({
                table_name: z.string().describe("LanceDB table name, e.g. 'audio_vibe_gpu'"),
                query_text: z.string().describe("Natural language query for vector search"),
                limit: z.number().describe("Max results to return"),
              }),
              execute: async ({ table_name, query_text, limit }) => {
                const res = await fetch(`${baseUrl}/query/lancedb`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ table_name, query_vector_description: query_text, limit }),
                });
                return await res.text();
              },
            },
            queryDuckDB: {
              description: "Run a SQL query against the DuckDB structured database",
              parameters: z.object({
                sql_query: z.string().describe("SQL query to execute against DuckDB"),
              }),
              execute: async ({ sql_query }) => {
                const res = await fetch(`${baseUrl}/query/duckdb`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ sql_query }),
                });
                return await res.text();
              },
            },
            discoverSchema: {
              description: "Discover column schema for a DuckDB or LanceDB table",
              parameters: z.object({
                table_name: z.string().describe("Table name to inspect"),
                db_type: z.string().describe("Database type: 'duckdb' or 'lancedb'"),
              }),
              execute: async ({ table_name, db_type }) => {
                const res = await fetch(`${baseUrl}/db/discover_schema`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ table_name, db_type }),
                });
                return await res.text();
              },
            },

            // ── RAG Query (was unused before!) ────────────────────
            queryRAG: {
              description: "Query the RAG service for retrieval-augmented generation (port 8005)",
              parameters: z.object({
                query: z.string().describe("Natural language query for RAG retrieval"),
              }),
              execute: async ({ query }) => {
                const res = await fetch(`${ragUrl}/query`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ query }),
                });
                return await res.text();
              },
            },

            // ── LLM Inference ──────────────────────────────────────
            inferenceLocal: {
              description: "Run text inference via local Phi/Ollama LLM on the GPU box",
              parameters: z.object({
                prompt: z.string().describe("The prompt to send to the local LLM"),
                context: z.string().describe("Optional context to include"),
              }),
              execute: async ({ prompt, context }) => {
                const res = await fetch(`${baseUrl}/inference/text`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ prompt, context }),
                });
                return await res.text();
              },
            },
            inferenceOpenRouter: {
              description: "Run text inference via OpenRouter API (Gemma, DeepSeek, etc.)",
              parameters: z.object({
                prompt: z.string().describe("The prompt to send"),
                context: z.string().describe("Optional context"),
                model: z.string().describe("Model ID, e.g. 'google/gemma-4-26b-a4b-it:free'"),
              }),
              execute: async ({ prompt, context, model }) => {
                const res = await fetch(`${baseUrl}/inference/openai`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ prompt, context, model }),
                });
                return await res.text();
              },
            },

            // ── Audio & DSP ────────────────────────────────────────
            generateAudio: {
              description: "Generate audio using Audiocraft/MusicGen from a text prompt",
              parameters: z.object({
                text_prompt: z.string().describe("Description of the audio to generate"),
                duration: z.number().describe("Duration in seconds"),
              }),
              execute: async ({ text_prompt, duration }) => {
                const res = await fetch(`${baseUrl}/generate/audio`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ text_prompt, duration }),
                });
                return await res.text();
              },
            },
            masterAudio: {
              description: "Master an audio file using the Sovereign ONNX neural mastering pipeline",
              parameters: z.object({
                file_path: z.string().describe("Absolute path to the WAV/FLAC audio file to master"),
              }),
              execute: async ({ file_path }) => {
                const res = await fetch(`${baseUrl}/master-audio`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ file_path }),
                });
                return await res.text();
              },
            },

            // ── OS & Filesystem ────────────────────────────────────
            readFile: {
              description: "Read a file from the local filesystem",
              parameters: z.object({
                filepath: z.string().describe("Absolute path to the file to read"),
              }),
              execute: async ({ filepath }) => {
                const res = await fetch(`${baseUrl}/os/read_file`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ filepath }),
                });
                return await res.text();
              },
            },
            writeFile: {
              description: "Write content to a file on the local filesystem",
              parameters: z.object({
                filepath: z.string().describe("Absolute path to the file to write"),
                content: z.string().describe("Content to write to the file"),
              }),
              execute: async ({ filepath, content }) => {
                const res = await fetch(`${baseUrl}/os/write_file`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ filepath, content }),
                });
                return await res.text();
              },
            },
            executeShell: {
              description: "Execute a shell command on the local machine",
              parameters: z.object({
                command: z.string().describe("Shell command to execute"),
              }),
              execute: async ({ command }) => {
                const res = await fetch(`${baseUrl}/os/execute_shell`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ command }),
                });
                return await res.text();
              },
            },
            findFiles: {
              description: "Find files matching a glob pattern on the local filesystem",
              parameters: z.object({
                pattern: z.string().describe("Glob pattern, e.g. 'C:/WEB CASE STUDY/**/*.py'"),
              }),
              execute: async ({ pattern }) => {
                const res = await fetch(`${baseUrl}/os/find_files`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ pattern }),
                });
                return await res.text();
              },
            },
            tailLog: {
              description: "Read the last N lines of a log file for real-time monitoring",
              parameters: z.object({
                filepath: z.string().describe("Absolute path to the log file"),
                lines: z.number().describe("Number of trailing lines to read"),
              }),
              execute: async ({ filepath, lines }) => {
                const res = await fetch(`${baseUrl}/os/tail_log`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ filepath, lines }),
                });
                return await res.text();
              },
            },
            runPythonFile: {
              description: "Execute a Python script file on the local machine",
              parameters: z.object({
                filepath: z.string().describe("Absolute path to the Python script"),
              }),
              execute: async ({ filepath }) => {
                const res = await fetch(`${baseUrl}/os/run_python_file`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ filepath }),
                });
                return await res.text();
              },
            },

            // ── Firebase / Firestore ───────────────────────────────
            readFirebaseDoc: {
              description: "Read a document from Firestore vault by doc_id",
              parameters: z.object({
                doc_id: z.string().describe("Firestore document ID to read"),
              }),
              execute: async ({ doc_id }) => {
                const res = await fetch(`${baseUrl}/firebase/read/${doc_id}`);
                return await res.text();
              },
            },
            listFirebaseCollections: {
              description: "List all top-level Firestore collections",
              parameters: z.object({}),
              execute: async () => {
                const res = await fetch(`${baseUrl}/firebase/collections`);
                return await res.text();
              },
            },

            // ── Browser Automation ─────────────────────────────────
            listBrowserTabs: {
              description: "List all open Edge browser tabs",
              parameters: z.object({}),
              execute: async () => {
                const res = await fetch(`${baseUrl}/browser/tabs`);
                return await res.text();
              },
            },
            openBrowserTab: {
              description: "Open a new Edge browser tab to a URL",
              parameters: z.object({
                url: z.string().describe("URL to open in a new tab"),
              }),
              execute: async ({ url }) => {
                const res = await fetch(`${baseUrl}/browser/new`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ url }),
                });
                return await res.text();
              },
            },

            // ── Tasks ──────────────────────────────────────────────
            listTasks: {
              description: "List all background tasks running on the local swarm",
              parameters: z.object({}),
              execute: async () => {
                const res = await fetch(`${baseUrl}/system/tasks`);
                return await res.text();
              },
            },

            // ── LangGraph Workflow ─────────────────────────────────
            runWorkflow: {
              description: "Execute a LangGraph agent workflow by name",
              parameters: z.object({
                workflow_name: z.string().describe("Workflow name, e.g. 'chat_v4', 'dsp_alignment'"),
                initial_state: z.string().describe("JSON string of initial state for the workflow"),
              }),
              execute: async ({ workflow_name, initial_state }) => {
                const res = await fetch(`${baseUrl}/run_workflow`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ workflow_name, initial_state: JSON.parse(initial_state) }),
                });
                return await res.text();
              },
            },

            // ── MCP Generic Tool Execute ───────────────────────────
            executeMCPTool: {
              description: "Execute any registered MCP tool by name via /tools/execute",
              parameters: z.object({
                tool_name: z.string().describe("MCP tool name to execute"),
                tool_params: z.string().describe("JSON string of parameters for the tool"),
              }),
              execute: async ({ tool_name, tool_params }) => {
                const res = await fetch(`${baseUrl}/tools/execute`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ tool_name, parameters: JSON.parse(tool_params) }),
                });
                return await res.text();
              },
            },

            // ── Ray Serve (was broken — used string replace!) ──────
            querySovereignBrain: {
              description: "Query the Ray Serve Sovereign Brain ONNX neural engine",
              parameters: z.object({}),
              execute: async () => {
                const res = await fetch(`${serveUrl}/sovereign-brain`);
                return await res.text();
              },
            },
          },
        });

        // Collect all tool results from all steps
        const toolResults: any[] = [];
        for (const step of response.steps) {
          if (step.toolResults) {
            for (const tr of step.toolResults) {
              toolResults.push({ toolName: tr.toolName, result: tr.result });
            }
          }
        }

        return Response.json({
          result: response.text || (toolResults.length > 0 ? JSON.stringify(toolResults) : "No response generated."),
          toolCalls: response.toolCalls,
          toolResults,
          steps: response.steps.length,
        }, { headers: CORS_HEADERS });
      } catch (err: any) {
        return Response.json({
          result: `Edge AI error: ${err.message}. Try a different prompt or check wrangler logs.`,
          error: err.message,
        }, { status: 500, headers: CORS_HEADERS });
      }
    }

    return new Response("Legion Edge Worker Active", { status: 200, headers: CORS_HEADERS });
  },
};
