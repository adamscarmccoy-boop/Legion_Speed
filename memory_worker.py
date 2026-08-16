import os
import lancedb
import pyarrow as pa
from typing import List, Dict, Any
from datetime import datetime

# Lazy load sentence_transformers to speed up import if not used immediately
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print("[System] Loading SentenceTransformer for memory embedding...")
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            import subprocess
            import sys
            print("\033[93m[System] Installing sentence-transformers...\033[0m")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "sentence-transformers", "-q"])
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

class MemoryBank:
    """Manages all interactions with the LanceDB vector store."""
    def __init__(self, db_path: str = None):
        if db_path is None or "chroma" in db_path.lower():
            # Override chroma paths with our lancedb path
            db_path = os.environ.get("LANCEDB_PATH", "./vectors/lancedb_store")
        
        # Ensure directory exists
        os.makedirs(db_path, exist_ok=True)
            
        self.client = lancedb.connect(db_path)
        self.collection_name = "legion_memory"
        
        # Define schema for LanceDB
        self.schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("role", pa.string()),
            pa.field("text", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), 384)), # MiniLM uses 384 dims
            pa.field("timestamp", pa.int64())
        ])
        
        # Open or create table
        table_names = self.client.table_names()
        if self.collection_name in table_names:
            self.collection = self.client.open_table(self.collection_name)
        else:
            self.collection = self.client.create_table(self.collection_name, schema=self.schema)
            
        print(f"MemoryBank initialized, connected to LanceDB at {db_path}")

    def save_interaction(self, user: str, ai: str):
        """Saves a user prompt and AI response into the vector store."""
        print("Saving interaction to memory...")
        model = get_embedding_model()
        
        # Compute embeddings
        user_vec = model.encode(user).tolist()
        ai_vec = model.encode(ai).tolist()
        
        now = int(datetime.now().timestamp())
        
        # Prepare data batch
        data = [
            {
                "id": f"user_{now}",
                "role": "user",
                "text": user,
                "vector": user_vec,
                "timestamp": now
            },
            {
                "id": f"ai_{now}",
                "role": "ai",
                "text": ai,
                "vector": ai_vec,
                "timestamp": now
            }
        ]
        
        self.collection.add(data)

    def query_context(self, prompt: str) -> str:
        """Retrieves relevant context by matching prompts and reconstructing the full exchange."""
        print("Querying memory for context...")
        model = get_embedding_model()
        
        try:
            # Prevent querying empty table
            if len(self.collection) == 0:
                return ""
                
            query_vec = model.encode(prompt).tolist()
            
            # 1. Search for semantic hits
            hits = self.collection.search(query_vec).limit(3).to_list()
            
            # 2. Extract unique timestamps to reconstruct complete exchanges
            timestamps = list(set(hit.get("timestamp") for hit in hits if hit.get("timestamp")))
            
            context = []
            for ts in timestamps:
                # Query all rows matching this timestamp (user + AI)
                exchange = self.collection.search().where(f"timestamp == {ts}").to_list()
                # Sort so user comes before AI
                exchange.sort(key=lambda x: 0 if x.get("role") == "user" else 1)
                
                if len(exchange) >= 2:
                    user_text = next((x.get("text") for x in exchange if x.get("role") == "user"), "")
                    ai_text = next((x.get("text") for x in exchange if x.get("role") == "ai"), "")
                    context.append(f"--- Past Interaction Exchange ---\nUser: {user_text}\nLegion: {ai_text}\n")
            
            if context:
                return "\n".join(context)
            else:
                return ""
        except Exception as e:
            print(f"[Memory Warning] Query failed: {e}")
            return ""
            
    def get_count(self) -> int:
        """Helper to get total memory count."""
        try:
            return len(self.collection)
        except:
            return 0
