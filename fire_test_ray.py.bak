"""Ray-ified fire test for the lakehouse search.

Uses DuckDB to scan the mined_code Parquet, then runs the TF-IDF + KMeans
clustering in a Ray worker so the main process stays responsive.

Multiple queries run in parallel as Ray tasks.
"""
import os, sys, json, time
from pathlib import Path

import duckdb
import ray
from pydantic import BaseModel, Field
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer

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
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================

from sklearn.cluster import KMeans
import pandas as pd

PARQUET = r"C:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lakehouse_data/mined_code.parquet"

# ---------------- Pydantic output shapes (matches the source) ----------------
class MinedSymbol(BaseModel):
    symbol_name: str
    type: str
    source_file: str

class ClusterGroup(BaseModel):
    cluster_id: int
    signature_keywords: List[str]
    items: List[MinedSymbol]

class DynamicSearchReport(BaseModel):
    search_term: str
    total_matches_found: int
    clusters: List[ClusterGroup]
    parquet_path: str
    parquet_size_mb: float

# ---------------- Init Ray ----------------
if not ray.is_initialized():
    ray.init(num_cpus=os.cpu_count(), ignore_reinit_error=True, log_to_driver=False)

# ---------------- Per-query worker ----------------
@ray.remote
def search_and_cluster(query_word: str, k_clusters: int = 4, parquet_path: str = PARQUET):
    # Each worker opens its own DuckDB connection
    con = duckdb.connect()
    try:
        df = con.execute(
            f"""
            SELECT symbol_name, type, source_file, docstring, code_content
            FROM read_parquet('{parquet_path}')
            WHERE symbol_name ILIKE '%{query_word}%'
               OR docstring   ILIKE '%{query_word}%'
               OR code_content ILIKE '%{query_word}%'
            """
        ).fetchdf()
    finally:
        con.close()

    if df.empty:
        return {
            "search_term": query_word,
            "total_matches_found": 0,
            "clusters": [],
            "parquet_path": parquet_path,
        }

    # Vectorize + cluster
    df["combined"] = (
        df["symbol_name"].astype(str) + " "
        + df["docstring"].fillna("").astype(str) + " "
        + df["code_content"].fillna("").astype(str)
    )
    vectorizer = TfidfVectorizer(max_features=500, stop_words="english")
    tfidf = vectorizer.fit_transform(df["combined"])

    actual_k = min(k_clusters, len(df))
    kmeans = KMeans(n_clusters=actual_k, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(tfidf)

    terms = vectorizer.get_feature_names_out()
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]

    clusters = []
    for i in range(actual_k):
        cdf = df[df["cluster"] == i]
        top_terms = [terms[ind] for ind in order_centroids[i, :5]]
        items = [
            MinedSymbol(
                symbol_name=str(r["symbol_name"]),
                type=str(r["type"]),
                source_file=str(r["source_file"]),
            )
            for _, r in cdf.iterrows()
        ]
        clusters.append({
            "cluster_id": int(i),
            "signature_keywords": top_terms,
            "items": [m.model_dump() for m in items],
        })

    return {
        "search_term": query_word,
        "total_matches_found": int(len(df)),
        "clusters": clusters,
        "parquet_path": parquet_path,
    }

# ---------------- Run ----------------
QUERIES = ["AUTONOMOUS", "RHYTHM", "AUDIO", "PIPELINE", "CLUSTER"]
K = 4

parquet_size_mb = Path(PARQUET).stat().st_size / (1024 * 1024)
print(f"Parquet: {PARQUET}")
print(f"Size:    {parquet_size_mb:.2f} MB")
print(f"Queries: {QUERIES}")
print(f"k:       {K}")
print(f"Ray CPUs: {os.cpu_count()}")
print()

# Quick preview: total row count + column list
con = duckdb.connect()
preview = con.execute(f"SELECT COUNT(*) AS n FROM read_parquet('{PARQUET}')").fetchdf()
cols = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{PARQUET}')").fetchdf()
con.close()
print(f"Rows in parquet: {int(preview['n'].iloc[0]):,}")
print(f"Columns: {list(cols['column_name'])}")
print()

t0 = time.time()
futures = [search_and_cluster.remote(q, K, PARQUET) for q in QUERIES]
results = ray.get(futures)
elapsed = time.time() - t0

# Pretty-print + save
out_path = Path(r"C:\WEB CASE STUDY\fire_test_report.json")
out_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
print(f"Elapsed: {elapsed:.2f}s")
print(f"Wrote {out_path}\n")

for r in results:
    print("=" * 78)
    print(f"QUERY: {r['search_term']}   matches: {r['total_matches_found']}")
    print("=" * 78)
    if r["total_matches_found"] == 0:
        print("  (no matches)")
        continue
    for c in r["clusters"]:
        kw = ", ".join(c["signature_keywords"])
        print(f"\n  Cluster {c['cluster_id']}  ({len(c['items'])} items)  keywords: [{kw}]")
        # show up to 8 sample symbols
        for it in c["items"][:8]:
            print(f"     - {it['symbol_name']:<40}  ({it['type']:<10})  {Path(it['source_file']).name}")
        if len(c["items"]) > 8:
            print(f"     ... +{len(c['items'])-8} more")

ray.shutdown()