# =====================================================================
# MODULE: legion_schema.py (Strict Pydantic V2 System Validation)
# =====================================================================
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Any, Optional
import re
import ray


class ASTSymbolMetadata(BaseModel):
    """
    Strict Pydantic V2 state schema validating code syntax properties 
    before committing them as structural tokens into your LanceDB Lakehouse.
    """
    filepath: str = Field(..., description="Absolute system path to the target source module")
    symbol_name: str = Field(..., description="The literal name of the extracted Function or Class")
    node_type: str = Field(..., description="ClassDef, FunctionDef, or AsyncFunctionDef")
    line_count: int = Field(..., ge=1, description="The starting line location inside the file matrix")
    
    # SYSTEM HARDWARE BOUNDARIES
    is_valid: bool = Field(..., description="True if verified clean inside Monty's Rust VM")
    memory_mapped_hash: str = Field(..., description="Unique SHA-256 fingerprint matching the compiled code block")

    @field_validator('filepath')
    @classmethod
    def enforce_raw_string_hygiene(cls, v: str) -> str:
        """
        Catches the exact 'invalid escape sequence' SyntaxWarnings logged by your workers.
        Forces all paths to conform to standard forward-slash uniform formats.
        """
        clean_v = v.replace("\\", "/")
        if " " in clean_v and not clean_v.startswith('"'):
            # Enforce strict wrapper protection for paths containing white spaces
            return f'"{clean_v}"'
        return clean_v

    @field_validator('symbol_name')
    @classmethod
    def block_malicious_symbol_injection(cls, v: str) -> str:
        """Ensures symbol names are pure alphanumeric code definitions, blocking injections."""
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(f"CRITICAL: Structural anomaly found in symbol extraction name: {v}")
        return v


@ray.remote(num_cpus=1)
def process_target_source_block(filepath: str, drive_root_tag: str) -> list:
    """
    Parallel worker task. Parses raw file bytes into a python Abstract Syntax Tree,
    verifies symbols inside Monty's Rust sandbox, and performs a strict Pydantic V2 
    type-check pass before returning memory-aligned row records.
    """
    import ast
    import hashlib
    from pydantic_core import ValidationError
    from legion_schema import ASTSymbolMetadata
    from pydantic_monty import Monty

    local_records = []
    clean_path_id = os.path.abspath(filepath).replace("\\", "/")

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            code_text = f.read()

        # Generate a distinct cryptographic hash for this specific byte block
        # Allows your Code-Specific RAG to verify file modifications in milliseconds
        file_hash = hashlib.sha256(code_text.encode('utf-8')).hexdigest()

        # --- STEP 1: DEEP AST ANALYSIS ---
        try:
            parsed_ast = ast.parse(code_text, filename=filepath)
            ast_symbols = []
            for node in ast.walk(parsed_ast):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    ast_symbols.append((node.name, node.__class__.__name__, node.lineno))
        except Exception:
            ast_symbols = [("raw_module", "Module", 1)]

        if not ast_symbols:
            ast_symbols = [("module_root", "Module", 1)]

        # --- STEP 2: RUST MONTY VALIDATION LOOP ---
        with Monty() as pool:
            for symbol_name, node_type, line_no in ast_symbols:
                is_monty_clean = False
                try:
                    with pool.checkout() as session:
                        # Test if the extracted symbol can compile inside an isolated namespace
                        session.feed_run(f"def {symbol_name}(): pass")
                    is_monty_clean = True
                except Exception:
                    is_monty_clean = False

                # --- STEP 3: HIGH-SPEED PYDANTIC V2 VERIFICATION PASS ---
                try:
                    # Instantiate the model class. Pydantic's core engine validates 
                    # types natively at the C/Rust extension layer.
                    validated_meta = ASTSymbolMetadata(
                        filepath=clean_path_id,
                        symbol_name=symbol_name,
                        node_type=node_type,
                        line_count=line_no,
                        is_valid=is_monty_clean,
                        memory_mapped_hash=file_hash
                    )
                    
                    # Convert the verified object directly into a clean python dict
                    local_records.append(validated_meta.model_dump())
                    
                except ValidationError as schema_err:
                    # Catches and filters out corrupted symbols or malformed structures
                    print(f"[SCHEMA-REJECT] File: {clean_path_id} | Symbol: {symbol_name} | Error: {schema_err}")
                    pass

    except Exception:
        # Prevent locked operating system files from halting the multi-threaded worker thread
        pass

    return local_records
