export class EmbeddingService {
  async getEmbedding(query: string): Promise<number[] | null> {
    try {
      const response = await fetch("http://127.0.0.1:1234/v1/embeddings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "text-embedding-snowflake-arctic-embed-l-v2.0",
          input: query
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.data[0].embedding;
      } else {
        console.warn(`[LM STUDIO EMBEDDING WARNING] returned status ${response.status}`);
        return null;
      }
    } catch (e) {
      console.warn(`[LM STUDIO EMBEDDING WARNING] unreachable: ${e}`);
      return null;
    }
  }
}
