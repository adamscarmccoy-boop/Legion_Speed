import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import * as eventsource from "eventsource";

global.EventSource = eventsource.default || eventsource;

async function test() {
    console.log("Connecting to http://127.0.0.1:8005/sse...");
    const transport = new SSEClientTransport(new URL("http://127.0.0.1:8005/sse"));
    const client = new Client({ name: "TestClient", version: "1.0.0" }, { capabilities: {} });
    
    await client.connect(transport);
    console.log("Connected! Querying 'PaniniRagEngine'...");
    
    try {
        const result = await client.callTool({
            name: "semantic_code_search",
            arguments: { query: "PaniniRagEngine", limit: 2 }
        });
        
        console.log("\n--- RESULT ---");
        console.log(result.content[0].text);
        console.log("--------------\n");
    } catch (e) {
        console.error("Error calling tool:", e);
    }
    
    process.exit(0);
}

test();
