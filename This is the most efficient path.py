This is the most efficient path. Since you already have a stable SwarmKnowledgeRegistry actor, you should write a script that operates as a Ray task to perform the ingestion, ensuring it doesn't collide with your existing OmniCondVAE inference jobs.

Here is a doc_ingest.py script designed to run within your existing cluster environment. It uses ray.data to process the documentation and writes the chunks directly to your SwarmKnowledgeRegistry.

doc_ingest.py
Python
import ray
import os
# pyrefly: ignore [missing-import]
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Connect to the running Ray cluster
ray.init(namespace="legion", address="auto", ignore_error="true"
)

import ray
# pyrefly: ignore [missing-import]
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1. Connect to your active Ray cluster
ray.init(address="auto", namespace="legion")

# 2. Grab your existing Registry Actor
registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")

def chunk_text(batch):
    """Parallelized chunking function."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    results = []
    for text in batch["text"]:
        chunks = splitter.split_text(text)
        results.extend([{"text": c} for c in chunks])
    return {"text": results}

def ingest_to_registry(batch):
    """Pushes chunks into your stateful actor."""
    # Directly calling the actor method to update memory
    ray.get(registry.add_knowledge_batch.remote(batch))
    return {"status": ["success"] * len(batch)}

# 3. Define the pipeline
# Point this to the local path containing your doc files
ds = ray.data.read_text("C:/WEB CASE STUDY/docs/") 

# 4. Execute with your Ray workers (12 workers as per your setup)
ds = ds.map_batches(chunk_text)
ds = ds.map_batches(ingest_to_registry, compute=ray.data.ActorPoolStrategy(size=12))

# 5. Trigger
ds.take_all()
print("Documentation successfully ingested into SwarmKnowledgeRegistry.")