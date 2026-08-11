/**
 * Defines the minimal interface for the LM Studio AI object provided to the plugin.
 */
export interface LMStudioAI {
    /**
     * Generates an embedding for the given text using the currently loaded embedding model in LM Studio.
     * @param text The text to generate an embedding for.
     * @returns A Promise that resolves to an array of numbers representing the embedding vector.
     */
    getEmbedding(text: string): Promise<number[]>;
}

/**
 * `LMStudioRouter` acts as a singleton gateway to LM Studio's native JavaScript AI functionalities,
 * automatically handling dynamic embedding dimension detection (1024-D Snowflake vs 768-D Nomic)
 * and providing resilient zero-crash fallback.
 */
export class LMStudioRouter {
    private static instance: LMStudioRouter;
    private ai: LMStudioAI | null = null;
    private detectedDimension: number | null = null;

    /**
     * Private constructor to enforce the singleton pattern.
     */
    private constructor() {}

    /**
     * Retrieves the singleton instance of `LMStudioRouter`.
     */
    public static getInstance(): LMStudioRouter {
        if (!LMStudioRouter.instance) {
            LMStudioRouter.instance = new LMStudioRouter();
        }
        return LMStudioRouter.instance;
    }

    /**
     * Sets the `LMStudioAI` context provided by LM Studio's JavaScript runtime.
     */
    public setAIContext(aiContext: LMStudioAI): void {
        this.ai = aiContext;
        console.log("[LMStudioRouter] LM Studio JavaScript AI context set successfully.");
    }

    /**
     * Generates an embedding for the given text using LM Studio's loaded embedding model.
     * Auto-detects whether the returned vector is 1024-D (Snowflake) or 768-D (Nomic).
     */
    public async generateEmbedding(text: string): Promise<number[]> {
        // 1. Primary: Native LM Studio JS SDK AI Context
        if (this.ai) {
            try {
                const vec = await this.ai.getEmbedding(text);
                if (vec && vec.length > 0) {
                    this.detectedDimension = vec.length;
                    return vec;
                }
            } catch (err) {
                console.warn("[LMStudioRouter] Native AI context error, falling back to local endpoint:", err);
            }
        }

        // 2. Resilient Fallback: Local LM Studio REST endpoint over loopback
        try {
            const response = await fetch("http://127.0.0.1:1234/v1/embeddings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    input: text,
                    model: "text-embedding-snowflake-arctic-embed-l-v2.0"
                })
            });

            if (response.ok) {
                const data = (await response.json()) as any;
                const vec = data.data[0].embedding;
                this.detectedDimension = vec.length;
                return vec;
            }
        } catch (fetchErr) {
            console.error("[LMStudioRouter] HTTP Fallback failed:", fetchErr);
        }

        throw new Error("[LMStudioRouter] Failed to generate embedding via JS Context or HTTP fallback.");
    }

    /**
     * Returns the detected dimension of the active embedding model (default 1024).
     */
    public getEmbeddingDimension(): number {
        return this.detectedDimension || 1024;
    }
}
