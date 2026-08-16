import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

async function testWorker() {
  console.log("Connecting to local Cloudflare Worker MCP server...");
  const transport = new SSEClientTransport(new URL("http://127.0.0.1:8787/mcp"));
  
  const client = new Client(
    { name: "test-client", version: "1.0.0" },
    { capabilities: {} }
  );

  await client.connect(transport);
  console.log("Connected successfully!");

  console.log("Listing available tools:");
  const tools = await client.listTools();
  console.dir(tools.tools, { depth: null });

  console.log("\nExecuting 'cloud_search' tool with query 'Chris Lake':");
  const result = await client.callTool({
    name: "cloud_search",
    arguments: { query: "Chris Lake" }
  });

  console.log("Tool execution result:");
  console.dir(result, { depth: null });

  console.log("\nClosing connection...");
  // Quick exit after test
  process.exit(0);
}

testWorker().catch(err => {
  console.error("Test failed:", err);
  process.exit(1);
});
