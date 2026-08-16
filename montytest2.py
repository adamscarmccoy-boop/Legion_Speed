import sys
import json
import time
import inspect
from typing import Dict, Any

try:
    import pydantic_monty as monty
    HAS_MONTY = True
except ImportError:
    HAS_MONTY = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def extract_package_telemetry() -> Dict[str, Any]:
    """
    Reflects on pydantic_monty at runtime to pull actual classes, 
    methods, attributes, and docstrings.
    """
    if not HAS_MONTY:
        return {"error": "pydantic_monty is not installed in the active venv."}

    module_dir = dir(monty)
    inspect_data = {
        "module_name": "pydantic_monty",
        "module_attributes": module_dir,
        "exported_members": {}
    }

    for attr_name in module_dir:
        if attr_name.startswith("__") and attr_name != "__doc__":
            continue
        try:
            attr_val = getattr(monty, attr_name)
            attr_type = str(type(attr_val))
            
            member_info = {
                "type": attr_type,
                "callable": callable(attr_val)
            }

            # If it's a class or function, extract signatures/methods
            if inspect.isclass(attr_val):
                member_info["class_methods"] = [m for m in dir(attr_val) if not m.startswith("__")]
                if hasattr(attr_val, "__doc__"):
                    member_info["docstring"] = str(attr_val.__doc__)[:200]
            elif callable(attr_val):
                try:
                    member_info["signature"] = str(inspect.signature(attr_val))
                except Exception:
                    member_info["signature"] = "Builtin / C-Extension (No inspection signature)"

            inspect_data["exported_members"][attr_name] = member_info
        except Exception as err:
            inspect_data["exported_members"][attr_name] = {"error": str(err)}

    return inspect_data


def prompt_nemotron_for_data_driven_fix(telemetry: Dict[str, Any]) -> None:
    """
    Sends raw module metadata to Nemotron and forces it to output a 
    data-backed code fix.
    """
    if not HAS_OPENAI:
        print("⚠️ `openai` library not found.")
        return

    print("=" * 80)
    print("📡 SENDING RUNTIME REFLECTION DATA TO NEMOTRON FOR DIAGNOSIS...")
    print("=" * 80)

    client = OpenAI(
        base_url="http://127.0.0.1:1234/v1",
        api_key="lm-studio"
    )

    prompt = f"""
You are the Lead Core Engineer debugging a Python VM wrapper.
Below is the exact runtime reflection payload (dir(), type(), docstrings, signatures) extracted directly from `pydantic_monty` in our live venv:

{json.dumps(telemetry, indent=2)}

DIAGNOSIS TASK:
1. Identify the EXACT method or class initializer exposed by `pydantic_monty` for evaluating Python code strings.
2. Explain specifically why calling `m_instance.eval(code)` or `monty.eval()` failed (cite exported members/types from the JSON payload above).
3. Provide a minimal 3-line Python snippet showing the exact syntax to run a code string so `successes` increases on every pass.
4. Base your answer STRICTLY on the reflection data provided above. Do NOT hallucinate methods that do not exist in the JSON payload.
"""

    start_t = time.perf_counter()
    response = client.chat.completions.create(
        model="nvidia/nemotron-3-nano-4b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    elapsed_ms = (time.perf_counter() - start_t) * 1000

    print(f"\n✅ [NEMOTRON RESPONDED IN {elapsed_ms:.2f} ms]:")
    print("-" * 80)
    print(response.choices[0].message.content)
    print("-" * 80)


if __name__ == "__main__":
    telemetry = extract_package_telemetry()
    print("📊 RAW PACKAGE REFLECTION TELEMETRY:")
    print(json.dumps(telemetry, indent=2))
    print("\n")
    prompt_nemotron_for_data_driven_fix(telemetry)