import os
import re
import sys
import json
import traceback

TARGET_DIR = r"C:\WEB CASE STUDY"

def repair_dunders(text: str) -> str:
    """Repairs markdown-bold mangled dunders (e.g., **name** -> __name__)."""
    repaired = re.sub(r'\*\*([a-zA-Z0-9_]+)\*\*', r'__\1__', text)
    return repaired.replace("**name**", "__name__").replace("**main**", "__main__")

def apply_surgical_patch(filename: str, search_block: str, replace_block: str) -> str:
    """
    Surgically replaces a specific code block in a file and compiles the result
    to verify syntax before saving to disk. Prevents token starvation by 
    completely eliminating massive monolithic file rewrites.
    """
    # Safety resolution for relative filenames
    filepath = os.path.join(TARGET_DIR, filename) if not os.path.isabs(filename) else filename
    
    if not os.path.exists(filepath):
        return json.dumps({
            "status": "FAILED", 
            "error": f"File '{filepath}' not found on disk. Cannot apply surgical patch."
        })
    
    try:
        # Load original file content
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # Clean and repair dunder/markdown artifacts in blocks
        cleaned_search = repair_dunders(search_block).strip()
        cleaned_replace = repair_dunders(replace_block).strip()

        # Normalize line endings to avoid carriage return mismatch issues
        cleaned_original_norm = original_content.replace('\r\n', '\n')
        cleaned_search_norm = cleaned_search.replace('\r\n', '\n')
        cleaned_replace_norm = cleaned_replace.replace('\r\n', '\n')

        # Attempt exact match block replacement
        if cleaned_search_norm not in cleaned_original_norm:
            # Fuzzy match fallback: Try matching line by line stripping leading/trailing whitespace
            search_lines = [l.strip() for l in cleaned_search_norm.split('\n') if l.strip()]
            original_lines = cleaned_original_norm.split('\n')
            
            match_start = -1
            match_end = -1
            n_search = len(search_lines)
            
            for i in range(len(original_lines) - n_search + 1):
                sub_window = [l.strip() for l in original_lines[i:i+n_search] if l.strip()]
                if sub_window == search_lines:
                    match_start = i
                    match_end = i + n_search
                    break
            
            if match_start != -1:
                # Found window match, substitute the lines
                before_part = "\n".join(original_lines[:match_start])
                after_part = "\n".join(original_lines[match_end:])
                patched_content = f"{before_part}\n{cleaned_replace_norm}\n{after_part}"
            else:
                # Direct match and fuzzy window both failed
                truncated_preview = cleaned_original_norm[:1500] + "\n... [TRUNCATED FOR CONTEXT LIMIT] ..." if len(cleaned_original_norm) > 1500 else cleaned_original_norm
                return json.dumps({
                    "status": "FAILED",
                    "error": "The specified SEARCH block was not found inside the target file. Check indentation and keywords.",
                    "target_file_preview": truncated_preview
                })
        else:
            # Clean exact match replacement
            patched_content = cleaned_original_norm.replace(cleaned_search_norm, cleaned_replace_norm)

        # Pre-flight syntax validation check (AST check)
        try:
            compile(patched_content, filepath, 'exec')
        except SyntaxError as syntax_err:
            tb_lines = traceback.format_exception_only(type(syntax_err), syntax_err)
            return json.dumps({
                "status": "REJECTED_BY_PREFLIGHT",
                "error": "Syntax compilation failed after applying surgical patch. Patch NOT written to disk.",
                "traceback": "".join(tb_lines)
            })

        # Save clean compile-verified code to disk
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(patched_content)

        return json.dumps({
            "status": "SUCCESS",
            "message": f"Surgical patch successfully applied, compile-verified (AST check PASSED), and written to disk at: {filepath}."
        })

    except Exception as e:
        return json.dumps({
            "status": "FAILED",
            "error": f"Autonomic patching failure: {str(e)}"
        })
