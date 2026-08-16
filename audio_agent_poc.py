import duckdb
import ollama
from pydantic import BaseModel, Field
from jinja2 import Template
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# =====================================================================
# ISOLATED JINJA PROMPT TEMPLATE BLUEPRINT
# =====================================================================
JINJA_ACOUSTIC_EXAMINER = """
System: You are an expert Audio Mastering AI.
Analyze the following acoustic vector data extracted from a track via DuckDB.
You must output a single JSON object matching the requested schema layout.

Acoustic Data Dump:
{% for row in track_data %}
* Segment: {{ row[2] }} -> RMS: {{ row[3] }}, Crest Factor: {{ row[4] }}, Sub-Bass: {{ row[11] }}, High-Energy: {{ row[14] }}, Semantic: {{ row[17] }}
{% endfor %}

User Query: {{ query }}
"""

# =====================================================================
# PYDANTIC MUZZLE (FIREWALL)
# =====================================================================
class AcousticAuditReport(BaseModel):
    """Pydantic Muzzle for LLM Acoustic Evaluation"""
    table_source: str = Field(..., description="Target Parquet data partition evaluated")
    processed_row_count: int
    anomalous_metric_detected: bool
    rms_health: str = Field(..., description="Evaluation of the RMS loudness values")
    crest_factor_health: str = Field(..., description="Evaluation of the crest factor (punchiness vs squashed)")
    structural_monologue: str = Field(..., description="Detailed instructions on the acoustic health and any needed DSP")


# =====================================================================
# DETACHED REASONING CONNECTIVITY LAYER
# =====================================================================
def analyze_audio_with_phi3(parquet_file_path: str, user_request: str) -> AcousticAuditReport:
    """
    Queries cold storage Parquet rows via projection pushdowns and uses 
    local Phi-3 constraints to return verified, token-muzzled Pydantic analytics.
    """
    con = duckdb.connect(database=":memory:")
    con.execute("SET threads=4;")
    
    logging.info(f"💾 Reading Parquet via DuckDB: {parquet_file_path}")
    
    # Extract records directly out of your local binary Parquet files
    raw_db_rows = con.execute(f"""
        SELECT 
            track_name, filepath, segment_name, rms, crest_factor, 
            zero_crossing_rate, spectral_centroid, spectral_bandwidth, 
            spectral_rolloff, spectral_flatness, spectral_contrast, 
            sub_bass_energy, bass_energy, mid_energy, high_energy, 
            mfcc_vector, chroma_vector, semantic_text
        FROM read_parquet('{parquet_file_path}')
    """).fetchall()
    
    # Compile prompt by feeding rows into separate Jinja template
    jinja_compiler = Template(JINJA_ACOUSTIC_EXAMINER)
    fully_rendered_prompt = jinja_compiler.render(
        track_data=raw_db_rows,
        query=user_request
    )
    
    logging.info("🧠 Passing structural math array into Ollama Phi-3...")
    
    # Pass the prompt to your offline model execution engine
    response = ollama.chat(
        model="phi3",
        messages=[{"role": "user", "content": fully_rendered_prompt}],
        options={"temperature": 0.0},
        format=AcousticAuditReport.model_json_schema()  # <-- THE MUZZLE LINK
    )
    
    raw_ai_string = response['message']['content']
    
    logging.info("🛡️ Enforcing Pydantic Firewall schema validation...")
    validated_insight = AcousticAuditReport.model_validate_json(raw_ai_string)
    
    return validated_insight

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print(" 🤖 Acoustic Audit Agent - Pydantic Firewall PoC")
    print("=" * 60)
    
    # Data path injected based on the system_data_audit_report.json
    test_parquet = r"C:\STUDIES_BACKUP\data\metadata\parquet_exports\37. Chris Lake_ Ragie Ban - Toxic _Extended Mix_.parquet"
    query = "Does this track have a commercial club-ready sub-bass and RMS? Compare it conceptually."
    
    try:
        result = analyze_audio_with_phi3(test_parquet, query)
        print("\n✅ Validated LLM JSON Response:\n")
        print(json.dumps(result.model_dump(), indent=2))
    except Exception as e:
        logging.error(f"❌ Error during execution: {e}")
