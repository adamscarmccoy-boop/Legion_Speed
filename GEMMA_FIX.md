404 Not Found error from OpenRouter.
`openai.NotFoundError: Error code: 404 - {'error': {'message': 'No endpoints found for google/gemma-2-9b-it.', 'code': 404}...}`.
The user wants to switch from OpenRouter to Google AI Studio (Gemini API) and use the "Gemma 4 31B" model (Note: The user says "Gemma 4 31B", but as of current real-world knowledge, Gemma 2 is the current stable family. However, I must follow the user's intent to use the Google AI Studio SDK/API specifically).
`legion_langgraph_brain.py`.

    *   *LLM Initialization:* The code currently uses `ChatGoogleGenerativeAI` (which is the correct class for Google AI Studio), but it's clearly still hitting an OpenRouter endpoint based on the error log.
    *   *Wait, looking closer at the code:*
        ```python
        self.llm = ChatGoogleGenerativeAI(
            model="gemma-4-31b-it",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7,
        )
        ```
    *   *The Mystery:* If the user is using `ChatGoogleGenerativeAI`, why is the log showing a request to `https://openrouter.ai/api/v1/chat/completions`?
    *   *Answer:* The `ChatGoogleGenerativeAI` class in `langchain-google-genai` does *not* hit OpenRouter. The error log provided by the user shows `httpx - INFO - HTTP Request: POST https://openrouter.ai/...`. This means that *somewhere* in the execution environment, the LLM is being instantiated as a `ChatOpenAI` object pointing to OpenRouter, OR the user is running a different version of the code than what they pasted, OR they have a global wrapper/bridge (like the `api_bridge` mentioned in the error logs) that is intercepting calls.
    *   *Crucial Observation:* The error log says `api_bridge - ERROR`. This suggests the user has a custom module or wrapper called `api_bridge` that is routing requests to OpenRouter regardless of the LangChain class used, or they are using `ChatOpenAI` in the actual running script.

    *   *Model Name:* The user specified "Gemma 4 31B". In Google AI Studio, the models usually follow names like `gemini-1.5-pro`, `gemini-1.5-flash`, or specific Gemma versions (e.g., `gemma-2-27b-it`). *Self-correction:* Since the user explicitly asked for a "Gemma 4" (which doesn't officially exist yet in the public domain as of my training, but I should treat it as the target string the user wants), I will use the string they provided, but I should warn them that the exact model string must match Google AI Studio's naming convention.
    *   *Authentication:* Ensure `GOOGLE_API_KEY` is used.
    *   *Dependency:* Ensure `langchain-google-genai` is installed.

    *   The error logs mention `api_bridge`. I need to tell the user to check if they have a wrapper that is overriding their LLM configuration.
    *   The logs show `google/gemma-2-9b-it` was being requested. This is a classic OpenRouter model string. The pasted code says `gemma-4-31b-it`. This confirms the code the user *is running* is not the code they *pasted*.

    *   *Step 1: Update LLM Initialization.* (Already mostly there, but ensure the model name is correct for Google AI Studio).
    *   *Step 2: Check environment variables.* Ensure `GOOGLE_API_KEY` is set and `OPENROUTER_API_KEY` isn't accidentally being used to route requests via a bridge.
    *   *Step 3: Fix the "api_bridge" conflict.* If they have a file called `api_bridge.py` or are importing a bridge, that's what's causing the 404 from OpenRouter.
    *   *Step 4: Correct the Model Name.* Google AI Studio uses specific IDs. `gemma-2-27b-it` is the actual high-parameter Gemma model. I will provide the correct naming convention.