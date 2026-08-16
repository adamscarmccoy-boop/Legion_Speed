import os
import sys
import lancedb
import pandas as pd
import numpy as np
import ray
import urllib.request
import json

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal
def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write('\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...')
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write('[LMS LIFECYCLE] Active Ray session detected. Disconnecting...')
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)
atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)

# Reconfigure stdout to prevent CP1252 character map crashes on unicode symbols
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def get_snowflake_vector(text):
    """Query local LM Studio on port 1234 for 1024-dim Snowflake embeddings."""
    payload = {
        "input": [text],
        "model": "text-embedding-snowflake-arctic-embed-l-v2.0"
    }
    req = urllib.request.Request(
        'http://localhost:1234/v1/embeddings',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        # STRICT TIMEOUT to prevent hanging
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data['data'][0]['embedding']
    except Exception as e:
        print(f'[WARN] Local LM Studio not responding or model offline: {e}')
        return None

def find_correct_ray_cluster(expected_actor='SwarmKnowledgeRegistry'):
    """Probes multiple Ray instances to find the one hosting the Knowledge Registry."""
    potential_addresses = ['127.0.0.1:6379', '127.0.0.1:53678', 'auto']

    for addr in potential_addresses:
        try:
            print(f'Probing Ray cluster at {addr}...')
            ray.init(address=addr, namespace='legion', ignore_reinit_error=True)
            try:
                # Attempt to get the actor with a short timeout
                registry = ray.get_actor(expected_actor)
                ray.get(registry.get_registered_tables_summary.remote(), timeout=2)
                print(f'Successfully locked onto Ray cluster at {addr}')
                return addr
            except Exception:
                print(f'Actor {expected_actor} not found or unresponsive on {addr}.')
                ray.shutdown()
        except Exception as e:
            print(f'Could not connect to {addr}: {e}')
            ray.shutdown()

    return None

def main():
    print('=== Legion RAG Database Query Tool (Jinja Injected) ===')

    # DEFAULT QUERY
    query = 'audio mastering baseline'
    if len(sys.argv) > 1:
        query = sys.argv[1]
        
    if query == 'why doesnt the c++ engine start automatically in the kernel so it can connect to ray on its api':
        print('Please specify a query.')
        sys.exit(0)
    
    # 1. FIND THE CORRECT RAY CLUSTER
    correct_addr = find_correct_ray_cluster()
    if not correct_addr:
        print('FATAL: Could not find a Ray cluster hosting the SwarmKnowledgeRegistry.')
        sys.exit(1)
    
    # 2. CONNECT TO LANCEDB
    db_path = r'C:\\WEB CASE STUDY\\lancedb_web_intel_rag'
    if not os.path.exists(db_path):
        db_path = r'C:\\WEB CASE STUDY\\.vector_cache'
        
    print(f'Connecting to LanceDB at: {db_path}...')
    try:
        db = lancedb.connect(db_path)
    except Exception as e:
        print(f'Error connecting to LanceDB: {e}')
        sys.exit(1)
    
    query_vector = get_snowflake_vector(query)

    code_list = []
    doc_list = []
    tables = db.table_names()

    # SOURCE 1: Code Vector Search
    if 'mined_code_vectors' in tables:
        print(f'\nSearching Code base for: \"{query}\"...')
        code_tbl = db.open_table('mined_code_vectors')
        try:
            if query_vector:
                code_results = code_tbl.search(query_vector).limit(3).to_pandas()
            else:
                df = code_tbl.to_pandas()
                mask = df['code_content'].astype(str).str.contains(query, case=False, na=False)
                code_results = df[mask].head(3)
            if not code_results.empty:
                code_list = code_results.to_dict(orient='records')
        except Exception as e:
            print(f'Code search error: {e}')
            
    # SOURCE 2: Documentation Vector Search
    if 'mined_documentation_vectors' in tables:
        print(f'\nSearching Documentation for: \"{query}\"...')
        doc_tbl = db.open_table('mined_documentation_vectors')
        try:
            if query_vector:
                doc_results = doc_tbl.search(query_vector).limit(3).to_pandas()
            else:
                df = doc_tbl.to_pandas()
                mask = df['text'].astype(str).str.contains(query, case=False, na=False)
                doc_results = df[mask].head(3)
            if not doc_results.empty:
                doc_list = doc_results.to_dict(orient='records')
        except Exception as e:
            print(f'Documentation search error: {e}')

    # --- JINJA INJECTION LOGIC ---
    JINJA_RAG_TEMPLATE = '''
# \ud83e\udde0 RAG Context Payload for Query: "{{ query }}"

## \ud83d\udcdd Semantic Code Results
{% if code_list %}
{% for row in code_list %}
### [Result #{{ loop.index }}] File: {{ row.get('source_file', 'Unknown') }}
**Symbol:** {{ row.get('symbol_name', 'N/A') }}
```python
{{ row.get('code_content', '') | truncate(1500) }}
```
---
{% endfor %}
{% else %}
*No semantic code matches found.*
{% endif %}

## \ud83d\udcda Semantic Documentation Results
{% if doc_list %}
{% for row in doc_list %}
### [Match #{{ loop.index }}]
{{ row.get('text', '') }}
---
{% endfor %}
{% else %}
*No documentation matches found.*
{% endif %}'''

    print('\n\u2699\ufe0f Compiling RAG context via Jinja template...')
    jinja_compiler = Template(JINJA_RAG_TEMPLATE)
    rendered_prompt = jinja_compiler.render(
        query=query, 
        code_list=code_list, 
        doc_list=doc_list
    )
    
    out_file = 'ADAMSCARMCCOY_RAG_PROMPT.md'
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(rendered_prompt)
        
    print(f'\n\u2705 Jinja injection complete! Rendered prompt saved to {out_file}')

if __name__ == '__main__':
    main()

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    # Avoid raising SystemExit inside an atexit callback (which causes RuntimeWarnings)
    if args and isinstance(args[0], int):
        sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================
