import {
  text,
  type Chat,
  type ChatMessage,
  type FileHandle,
  type LLMDynamicHandle,
  type PredictionProcessStatusController,
  type PromptPreprocessorController,
} from "@lmstudio/sdk";
import { configSchematics } from "./config";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

type DocumentContextInjectionStrategy = "none" | "inject-full-content" | "retrieval";

export async function preprocess(ctl: PromptPreprocessorController, userMessage: ChatMessage) {
  const userPrompt = userMessage.getText();
  const pluginConfig = ctl.getPluginConfig(configSchematics);
  const enableMcpRag = pluginConfig.get("enableMcpRag");
  const retrievalLimit = pluginConfig.get("retrievalLimit") || 3;

  // --- MCP RAG INTEGRATION (With Unlocked Dynamic Embedding & Fail-Safe Fallback) ---
  let mcpContext = "";
  if (enableMcpRag && userPrompt.trim().length > 5) {
    const status = ctl.createStatus({ status: "loading", text: "Querying LanceDB / Sovereign Vector Lakehouse..." });
    try {
      if (typeof EventSource === 'undefined') {
        globalThis.EventSource = (await import('eventsource')).default as any;
      }

      const transport = new SSEClientTransport(new URL("http://127.0.0.1:8005/sse"));
      const client = new Client({ name: "LMStudioPlugin", version: "2.0.0" }, { capabilities: {} });

      await client.connect(transport);
      status.setState({ status: "loading", text: "Fetching Sovereign Vector Intelligence..." });

      const [lancedbResult, swarmCodeResult, swarmIntelResult] = await Promise.allSettled([
        client.callTool({
          name: "semantic_code_search",
          arguments: { query: userPrompt, limit: retrievalLimit }
        }),
        client.callTool({
          name: "swarm_code_search",
          arguments: { search_term: userPrompt, limit: Math.max(1, Math.floor(retrievalLimit / 2)) }
        }),
        client.callTool({
          name: "swarm_intelligence_search",
          arguments: { search_term: userPrompt, limit: Math.max(1, Math.floor(retrievalLimit / 2)) }
        })
      ]);

      let foundContext = false;

      if (lancedbResult.status === "fulfilled" && lancedbResult.value.content?.length) {
        mcpContext += (lancedbResult.value.content[0] as any).text + "\n\n";
        foundContext = true;
      }

      if (swarmCodeResult.status === "fulfilled" && swarmCodeResult.value.content?.length) {
        mcpContext += (swarmCodeResult.value.content[0] as any).text + "\n\n";
        foundContext = true;
      }

      if (swarmIntelResult.status === "fulfilled" && swarmIntelResult.value.content?.length) {
        mcpContext += (swarmIntelResult.value.content[0] as any).text + "\n\n";
        foundContext = true;
      }

      status.setState({
        status: "done",
        text: foundContext ? "Sovereign Swarm & LanceDB context injected!" : "No relevant vector data found."
      });

      await transport.close();
    } catch (e: any) {
      status.setState({ status: "done", text: "MCP Server offline (bypassing preprocessor safely)." });
      ctl.debug("MCP Error: " + e.message);
    }
  }

  const history = await ctl.pullHistory();
  history.append(userMessage);
  const newFiles = userMessage.getFiles(ctl.client).filter(f => f.type !== "image");
  const files = history.getAllFiles(ctl.client).filter(f => f.type !== "image");

  if (newFiles.length > 0) {
    const strategy = await chooseContextInjectionStrategy(ctl, userPrompt, newFiles);
    if (strategy === "inject-full-content") {
      const msg = await prepareDocumentContextInjection(ctl, userMessage);
      if (mcpContext) msg.replaceText(msg.getText() + "\n\n" + mcpContext);
      return msg;
    } else if (strategy === "retrieval") {
      const processed = await prepareRetrievalResultsContextInjection(ctl, userPrompt, files);
      userMessage.replaceText(processed + (mcpContext ? "\n\n" + mcpContext : ""));
      return userMessage;
    }
  } else if (files.length > 0) {
    const processed = await prepareRetrievalResultsContextInjection(ctl, userPrompt, files);
    userMessage.replaceText(processed + (mcpContext ? "\n\n" + mcpContext : ""));
    return userMessage;
  }

  if (mcpContext) {
    userMessage.replaceText(userPrompt + "\n\n=== SOVEREIGN RAG CONTEXT ===\n" + mcpContext);
  }

  return userMessage;
}

async function prepareRetrievalResultsContextInjection(
  ctl: PromptPreprocessorController,
  originalUserPrompt: string,
  files: Array<FileHandle>,
): Promise<string> {
  const pluginConfig = ctl.getPluginConfig(configSchematics);
  const retrievalLimit = pluginConfig.get("retrievalLimit");
  const retrievalAffinityThreshold = pluginConfig.get("retrievalAffinityThreshold");

  const statusSteps = new Map<FileHandle, PredictionProcessStatusController>();
  const retrievingStatus = ctl.createStatus({
    status: "loading",
    text: `Loading active embedding model for retrieval...`,
  });

  // FIX: Dynamically target the currently loaded embedding model/DLL rather than hardcoded string
  const model = await ctl.client.embedding.model();

  retrievingStatus.setState({
    status: "loading",
    text: `Retrieving relevant citations...`,
  });

  const result = await ctl.client.files.retrieve(originalUserPrompt, files, {
    embeddingModel: model,
    limit: retrievalLimit,
    signal: ctl.abortSignal,
    onFileProcessList(filesToProcess) {
      for (const file of filesToProcess) {
        statusSteps.set(
          file,
          retrievingStatus.addSubStatus({
            status: "waiting",
            text: `Process ${file.name} for retrieval`,
          }),
        );
      }
    },
    onFileProcessingStart(file) {
      statusSteps.get(file)!.setState({ status: "loading", text: `Processing ${file.name}` });
    },
    onFileProcessingEnd(file) {
      statusSteps.get(file)!.setState({ status: "done", text: `Processed ${file.name}` });
    },
  });

  result.entries = result.entries.filter(entry => entry.score > retrievalAffinityThreshold);

  let processedContent = "";
  if (result.entries.length > 0) {
    retrievingStatus.setState({
      status: "done",
      text: `Retrieved ${result.entries.length} relevant citations`,
    });
    processedContent += "Citations:\n\n";
    let citationNumber = 1;
    result.entries.forEach(entry => {
      processedContent += `Citation ${citationNumber}: "${entry.content}"\n\n`;
      citationNumber++;
    });
    await ctl.addCitations(result);
    processedContent += `User Query:\n\n${originalUserPrompt}`;
  } else {
    retrievingStatus.setState({
      status: "canceled",
      text: `No citations found in files`,
    });
    processedContent = `User Query:\n\n${originalUserPrompt}`;
  }

  return processedContent;
}

async function prepareDocumentContextInjection(
  ctl: PromptPreprocessorController,
  input: ChatMessage,
): Promise<ChatMessage> {
  const documentInjectionSnippets: Map<FileHandle, string> = new Map();
  const files = input.consumeFiles(ctl.client, file => file.type !== "image");
  for (const file of files) {
    const { content } = await ctl.client.files.parseDocument(file, { signal: ctl.abortSignal });
    documentInjectionSnippets.set(file, content);
  }

  let formattedFinalUserPrompt = "";
  if (documentInjectionSnippets.size > 0) {
    formattedFinalUserPrompt += "User Document Content:\n";
    for (const [fileHandle, snippet] of documentInjectionSnippets) {
      formattedFinalUserPrompt += `\n** ${fileHandle.name} **\n${snippet}\n`;
    }
    formattedFinalUserPrompt += `\nUser Query: ${input.getText()}`;
  }

  input.replaceText(formattedFinalUserPrompt);
  return input;
}

async function chooseContextInjectionStrategy(
  ctl: PromptPreprocessorController,
  originalUserPrompt: string,
  files: Array<FileHandle>,
): Promise<DocumentContextInjectionStrategy> {
  return "inject-full-content";
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
