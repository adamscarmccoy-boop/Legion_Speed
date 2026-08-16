"""
LEGION RAY LIVE PROBE
=====================
Purpose:
  Attach to the already-running Legion Ray cluster and interrogate the live
  SwarmKnowledgeRegistry actor without rebuilding anything.

Based on your existing dump:
  - ray.init(address="auto", namespace="legion") works
  - live named actor: SwarmKnowledgeRegistry
  - known good method: get_registered_tables_summary
  - Ray State API filter key should be ray_namespace, not namespace

Run from the machine where Ray is already running:
  python legion_ray_live_probe.py

Optional:
  python legion_ray_live_probe.py --actor SwarmKnowledgeRegistry --namespace legion
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def safe_json(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, default=str)
    except Exception:
        return repr(obj)


def call_actor_method(
    actor,
    method_name: str,
    *args,
    timeout_s: float = 20,
    **kwargs,
) -> Dict[str, Any]:
    import ray

    try:
        method = getattr(actor, method_name)
    except Exception as e:
        return {
            "method": method_name,
            "ok": False,
            "error": f"missing method: {type(e).__name__}: {e}",
        }

    try:
        ref = method.remote(*args, **kwargs)
        value = ray.get(ref, timeout=timeout_s)
        return {
            "method": method_name,
            "ok": True,
            "value": value,
        }
    except Exception as e:
        return {}