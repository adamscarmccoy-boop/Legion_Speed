ching for Gemma ONNX

I'm currently focused on locating and synthesizing information related to "Gemma ONNX" within the provided context. My search is actively examining files, including the path c:\Users\adams\.gemini\antigravity, for any relevant mentions or details.

Integrating Gemma ONNX

My current focus is on synthesizing the information found regarding "Gemma ONNX." I've identified implementation plans detailing the integration of GemmaONNXAgent to replace Phi3Agent and noted key technical requirements like CPU execution via onnxruntime-genai. I'm also reviewing tasks associated with this integration.

Synthesizing Gemma ONNX Details

I've been piecing together information about integrating Gemma ONNX. The plan involves replacing Phi3Agent with GemmaONNXAgent, ensuring CPU execution via onnxruntime-genai, and addressing tool calling syntax. I'm also noting the model's path as C:\WEB CASE STUDY\gemma_onnx and the need for it to handle LangChain messages.

It looks like you're working on integrating the google/gemma-2-2b-it model, compiled to ONNX, into your Pydantic LangGraph Brain. This involves replacing the existing Phi3Agent with a new GemmaONNXAgent that leverages the ONNX model for CPU-native execution.

Here's a summary of the key aspects regarding "Gemma ONNX" from your project context:

1. Goal of Integration: The primary goal is to swap out the Phi3Agent in C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\AI_Logs\pydantic\legion_langgraph_brain.py with a CPU-native google/gemma-2-2b-it ONNX execution agent (GemmaONNXAgent). This agent will route your six specialist tools (DuckDB, LanceDB, Parquet Analytics).

2. Technical Requirements and Constraints:

CPU-Native Execution: The model compilation and execution must run on the CPU to avoid running out of VRAM/memory, as your target machine has a single GTX 1650 (4GB VRAM) and 16GB system RAM.
onnxruntime-genai: You are using onnxruntime-genai for loading and executing the compiled Gemma model.
Model Path: The compiled Gemma ONNX model is expected to be located at C:\WEB CASE STUDY\gemma_onnx. There's a verification step to ensure this model exists or to run compile_gemma.py to generate it.
3. GemmaONNXAgent Implementation:

A GemmaONNXAgent class will be built to mirror the Phi3Agent interface.
It will ingest LangChain messages arrays, format them into Gemma's native chat template (<start_of_turn>user\n...<end_of_turn>), and pass them to the onnxruntime_genai.Model.
The class will also natively parse the text output back into LangChain tool_calls, similar to how Ollama currently handles it.
4. Tool Calling Challenge: Unlike Ollama/Llama 3.2, google/gemma-2-2b-it does not natively support tool-calling schemas directly in its API. This means you need to inject a system prompt to guide Gemma to output a structured JSON tool call (e.g., {"name": "...", "arguments": {...}}) which will then be parsed by your agent wrapper.

5. Verification: The integration will be verified by running the __main__ smoke test in legion_langgraph_brain.py to ensure Gemma successfully invokes the DuckDB and LanceDB tools natively on CPU.

6. Example of Raw ONNX Generation: The test_raw_onnx_greedy.py script demonstrates how to load the Gemma ONNX model and tokenizer from C:\WEB CASE STUDY\gemma_onnx and perform auto-regressive text generation using onnxruntime and onnxruntime_genai. It includes steps for encoding prompts, preparing inputs for the ONNX graph, running inference, and decoding generated tokens.

7. VS Code Extension Integration: A future plan involves integrating the GemmaONNXAgent with an Antigravity VS Code Extension. A FastAPI bridge (gemma_api_bridge.py) will expose an HTTP endpoint for the extension to communicate with ray.get_actor("GemmaONNXAgent"), allowing the LLM chat interface in the Webview to interact with your Gemma ONNX model.