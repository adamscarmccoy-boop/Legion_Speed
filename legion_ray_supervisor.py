"""
legion_ray_supervisor.py
========================
Durable Ray actor supervisor for the Legion / Sovereign audio stack.

What this does:
- Connects to an existing Ray cluster if available, otherwise starts local Ray.
- Uses namespace='legion'.
- Creates or retrieves named detached actors.
- Creates a compatible SwarmKnowledgeRegistry if your real one is not already running.
- Writes JSON + Markdown status reports so you can upload them back to ChatGPT.

Run:
    .venv\Scripts\python.exe legion_ray_supervisor.py boot
    .venv\Scripts\python.exe legion_ray_supervisor.py status
    .venv\Scripts\python.exe legion_ray_supervisor.py register-parquet "C:\path\file.parquet" --name my_table
    .venv\Scripts\python.exe legion_ray_supervisor.py dump

Important:
Ray actor state is memory state, not magically saved to parquet. Parquet is your durable table/data storage.
This supervisor keeps actors findable while Ray is running. For true persistence, dump actor state to disk.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
sys.path.append(r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline")
sys.path.append(r"C:\WEB CASE STUDY")
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import ray
except Exception as exc:  # pragma: no cover
    print(f"[FATAL] Could not import ray: {exc}")
    sys.exit(1)

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except Exception:
    pa = None
    pq = None

NAMESPACE = os.environ.get("LEGION_NAMESPACE", "legion")
OUT_DIR = Path(os.environ.get("LEGION_REPORT_DIR", r"C:\WEB CASE STUDY\ray_supervisor_exports"))
OUT_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# Small structured status payloads. Pydantic is not required for the supervisor
# itself because this file needs to boot even in a slightly broken environment.
# Your math actors should still use your Pydantic schemas at their boundaries.
# -----------------------------------------------------------------------------
@dataclass
class ActorStatus:
    name: str
    namespace: str
    state: str
    actor_type: str
    detail: str = ""
    methods: Optional[List[str]] = None


@dataclass
class SupervisorReport:
    created_at: str
    namespace: str
    ray_initialized: bool
    ray_address: str
    actors: List[ActorStatus]
    errors: List[str]


# -----------------------------------------------------------------------------
# Compatible fallback registry.
# This only appears if your existing SwarmKnowledgeRegistry is not running.
# It provides the methods your old scripts already expect.
# -----------------------------------------------------------------------------
@ray.remote
class SwarmKnowledgeRegistryCompat:
    def __init__(self) -> None:
        self.registry: Dict[str, Any] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.created_at = datetime.now().isoformat(timespec="seconds")

    def ping(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "actor": "SwarmKnowledgeRegistryCompat",
            "created_at": self.created_at,
            "tables": list(self.registry.keys()),
        }

    def register_table(self, name: str, table: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.registry[name] = table
        self.metadata[name] = metadata or {}
        return {"ok": True, "registered": name, "num_tables": len(self.registry)}

    def get_table(self, name: str) -> Any:
        if name not in self.registry:
            raise KeyError(f"Table not found in registry: {name}")
        return self.registry[name]

    def list_tables(self) -> List[str]:
        return sorted(self.registry.keys())

    def get_registered_tables_summary(self) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for name, obj in self.registry.items():
            info = dict(self.metadata.get(name, {}))
            info["python_type"] = type(obj).__name__
            try:
                info["num_rows"] = int(obj.num_rows)  # pyarrow Table
                info["num_columns"] = int(obj.num_columns)
                info["columns"] = list(obj.schema.names)
            except Exception:
                pass
            out[name] = info
        return out

    def dump_summary(self) -> Dict[str, Any]:
        return {
            "created_at": self.created_at,
            "tables": self.get_registered_tables_summary(),
        }


# -----------------------------------------------------------------------------
# Minimal supervisor actor. It does not own all other actors by handle only.
# It records names and health checks, so scripts can re-find actors by name.
# -----------------------------------------------------------------------------
@ray.remote
class LegionSupervisorActor:
    def __init__(self, namespace: str = NAMESPACE) -> None:
        self.namespace = namespace
        self.created_at = datetime.now().isoformat(timespec="seconds")
        self.actor_names: Dict[str, Dict[str, Any]] = {}

    def ping(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "actor": "LegionSupervisorActor",
            "namespace": self.namespace,
            "created_at": self.created_at,
            "known_actor_names": self.actor_names,
        }

    def remember_actor(self, logical_name: str, actor_name: str, actor_type: str, detail: str = "") -> Dict[str, Any]:
        self.actor_names[logical_name] = {
            "actor_name": actor_name,
            "actor_type": actor_type,
            "detail": detail,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        return {"ok": True, "remembered": logical_name, "actor_name": actor_name}

    def list_known_actors(self) -> Dict[str, Dict[str, Any]]:
        return dict(self.actor_names)


# -----------------------------------------------------------------------------
# Ray helpers
# -----------------------------------------------------------------------------
def init_ray(address: Optional[str] = "auto") -> str:
    """Connect to Ray. Try address=auto first, then local."""
    if ray.is_initialized():
        return "already_initialized"

    if address:
        try:
            ray.init(address=address, namespace=NAMESPACE, ignore_reinit_error=True)
            return str(address)
        except Exception as exc:
            print(f"[WARN] ray.init(address={address!r}) failed: {exc}")

    ray.init(namespace=NAMESPACE, ignore_reinit_error=True)
    return "local"


def get_actor_safe(name: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return ray.get_actor(name, namespace=NAMESPACE), None
    except Exception as exc:
        return None, str(exc)


def create_named_actor(actor_cls: Any, name: str, *args: Any, **kwargs: Any) -> Tuple[Any, str]:
    """Create or retrieve a named detached actor."""
    existing, err = get_actor_safe(name)
    if existing is not None:
        return existing, "existing"

    actor = actor_cls.options(
        name=name,
        namespace=NAMESPACE,
        lifetime="detached",
        get_if_exists=True,
    ).remote(*args, **kwargs)
    return actor, "created"


def import_actor_class(module_name: str, class_name: str) -> Tuple[Optional[Any], str]:
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        return cls, "ok"
    except Exception as exc:
        return None, f"{module_name}.{class_name}: {exc}"


def call_ping(actor: Any) -> Tuple[str, str, Optional[List[str]]]:
    """Try to ping actor. Return state/detail/methods."""
    try:
        methods = [m for m in dir(actor) if not m.startswith("_")][:50]
    except Exception:
        methods = None
    try:
        if hasattr(actor, "ping"):
            detail = ray.get(actor.ping.remote())
            return "ok", json.dumps(detail, default=str)[:2000], methods
        return "ok", "No ping() method; actor handle exists.", methods
    except Exception as exc:
        return "error", str(exc), methods


# -----------------------------------------------------------------------------
# Boot actors
# -----------------------------------------------------------------------------
def boot_supervisor(include_existing_stack: bool = True) -> SupervisorReport:
    ray_address = init_ray("auto")
    errors: List[str] = []
    statuses: List[ActorStatus] = []

    # 1. Supervisor itself
    supervisor, mode = create_named_actor(LegionSupervisorActor, "LegionSupervisor", NAMESPACE)
    state, detail, methods = call_ping(supervisor)
    statuses.append(ActorStatus("LegionSupervisor", NAMESPACE, state, "LegionSupervisorActor", f"{mode}: {detail}", methods))

    # 2. Registry: retrieve existing SwarmKnowledgeRegistry, else create compatible one.
    registry, err = get_actor_safe("SwarmKnowledgeRegistry")
    if registry is None:
        registry, mode = create_named_actor(SwarmKnowledgeRegistryCompat, "SwarmKnowledgeRegistry")
        detail_prefix = f"{mode} compat registry"
    else:
        detail_prefix = "existing registry"

    state, detail, methods = call_ping(registry)
    statuses.append(ActorStatus("SwarmKnowledgeRegistry", NAMESPACE, state, "SwarmKnowledgeRegistry/Compat", f"{detail_prefix}: {detail}", methods))
    try:
        ray.get(supervisor.remember_actor.remote("registry", "SwarmKnowledgeRegistry", "SwarmKnowledgeRegistry", detail_prefix))
    except Exception as exc:
        errors.append(f"Could not remember registry: {exc}")

    # 3. Try to create/retrieve known old actors. These are optional.
    if include_existing_stack:
        actor_specs = [
            # logical_name, actor_name, module, class, args_provider
            ("social", "SocialActor", "legion_sonic_engine_actors", "SocialActor", lambda: ()),
            ("marketing", "MarketingActor", "legion_sonic_engine_actors", "MarketingActor", lambda: ()),
            # WardenActor usually needs handles, so we skip automatic creation unless already exists.
            ("warden", "WardenActor", "legion_sonic_engine_actors", "WardenActor", None),
            ("dsp_alignment", "DSPAlignmentActor", "legion_sonic_engine_actors", "DSPAlignmentActor", lambda: (r"C:\STUDIES_BACKUP\vectors\lancedb_store",)),
            ("intelligence_bridge", "IntelligenceBridge", "legion_sonic_engine_orchestrator", "IntelligenceBridge", None),
            # Local Gemma ONNX remote actor
            ("gemma_onnx_agent", "GemmaONNXAgent", "gemma_onnx_server", "GemmaONNXAgent", lambda: ()),
        ]

        for logical, actor_name, module_name, class_name, args_provider in actor_specs:
            existing, _ = get_actor_safe(actor_name)
            if existing is not None:
                state, detail, methods = call_ping(existing)
                statuses.append(ActorStatus(actor_name, NAMESPACE, state, class_name, f"existing: {detail}", methods))
                try:
                    ray.get(supervisor.remember_actor.remote(logical, actor_name, class_name, "existing"))
                except Exception as exc:
                    errors.append(f"Could not remember {actor_name}: {exc}")
                continue

            if args_provider is None:
                statuses.append(ActorStatus(actor_name, NAMESPACE, "skipped", class_name, "needs constructor args or dependencies"))
                continue

            cls, msg = import_actor_class(module_name, class_name)
            if cls is None:
                statuses.append(ActorStatus(actor_name, NAMESPACE, "missing", class_name, msg))
                continue

            try:
                args = args_provider()
                actor, mode = create_named_actor(cls, actor_name, *args)
                state, detail, methods = call_ping(actor)
                statuses.append(ActorStatus(actor_name, NAMESPACE, state, class_name, f"{mode}: {detail}", methods))
                ray.get(supervisor.remember_actor.remote(logical, actor_name, class_name, mode))
            except Exception as exc:
                errors.append(f"Could not create {actor_name}: {exc}\n{traceback.format_exc()}")
                statuses.append(ActorStatus(actor_name, NAMESPACE, "error", class_name, str(exc)))

    return SupervisorReport(
        created_at=datetime.now().isoformat(timespec="seconds"),
        namespace=NAMESPACE,
        ray_initialized=ray.is_initialized(),
        ray_address=ray_address,
        actors=statuses,
        errors=errors,
    )


# -----------------------------------------------------------------------------
# Parquet registration and dumps
# -----------------------------------------------------------------------------
def register_parquet(path: str, name: Optional[str] = None) -> Dict[str, Any]:
    if pq is None:
        raise RuntimeError("pyarrow is required for parquet registration.")
    init_ray("auto")
    registry, err = get_actor_safe("SwarmKnowledgeRegistry")
    if registry is None:
        raise RuntimeError("SwarmKnowledgeRegistry is not running. Run: legion_ray_supervisor.py boot")

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    table_name = name or p.stem
    table = pq.read_table(str(p))
    meta = {
        "source_path": str(p),
        "registered_at": datetime.now().isoformat(timespec="seconds"),
        "num_rows": int(table.num_rows),
        "num_columns": int(table.num_columns),
        "columns": list(table.schema.names),
    }
    result = ray.get(registry.register_table.remote(table_name, table, meta))
    return {"result": result, "metadata": meta}


def dump_status() -> Dict[str, Any]:
    init_ray("auto")
    out: Dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "namespace": NAMESPACE,
        "actors": {},
    }
    for actor_name in [
        "LegionSupervisor",
        "SwarmKnowledgeRegistry",
        "SocialActor",
        "MarketingActor",
        "WardenActor",
        "DSPAlignmentActor",
        "IntelligenceBridge",
    ]:
        actor, err = get_actor_safe(actor_name)
        if actor is None:
            out["actors"][actor_name] = {"state": "missing", "error": err}
            continue
        state, detail, methods = call_ping(actor)
        out["actors"][actor_name] = {"state": state, "detail": detail, "methods": methods}
        if actor_name == "SwarmKnowledgeRegistry":
            for method in ["get_registered_tables_summary", "list_tables", "dump_summary"]:
                try:
                    if hasattr(actor, method):
                        out["actors"][actor_name][method] = ray.get(getattr(actor, method).remote())
                except Exception as exc:
                    out["actors"][actor_name][f"{method}_error"] = str(exc)
    return out


def write_report(prefix: str, payload: Any) -> Tuple[Path, Path]:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUT_DIR / f"{prefix}_{ts}.json"
    md_path = OUT_DIR / f"{prefix}_{ts}.md"

    def to_jsonable(obj: Any) -> Any:
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        if isinstance(obj, list):
            return [to_jsonable(x) for x in obj]
        if isinstance(obj, dict):
            return {k: to_jsonable(v) for k, v in obj.items()}
        return obj

    data = to_jsonable(payload)
    json_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    lines = [f"# {prefix}", "", f"Created: `{datetime.now().isoformat(timespec='seconds')}`", ""]
    lines.append("```json")
    lines.append(json.dumps(data, indent=2, default=str))
    lines.append("```")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Legion Ray durable actor supervisor")
    sub = parser.add_subparsers(dest="cmd", required=True)

    boot_p = sub.add_parser("boot", help="Boot/recover named detached actors")
    boot_p.add_argument("--minimal", action="store_true", help="Only boot supervisor + registry")

    sub.add_parser("status", help="Dump actor status")
    sub.add_parser("dump", help="Alias for status")

    reg_p = sub.add_parser("register-parquet", help="Load a parquet file into SwarmKnowledgeRegistry actor memory")
    reg_p.add_argument("path")
    reg_p.add_argument("--name", default=None)

    args = parser.parse_args()

    if args.cmd == "boot":
        report = boot_supervisor(include_existing_stack=not args.minimal)
        json_path, md_path = write_report("legion_ray_boot_report", report)
        print(f"[OK] Boot report JSON: {json_path}")
        print(f"[OK] Boot report MD:   {md_path}")
        for st in report.actors:
            print(f"[{st.state.upper()}] {st.name} :: {st.actor_type} :: {st.detail[:160]}")
        if report.errors:
            print("[WARN] Errors:")
            for err in report.errors:
                print(err[:1000])

    elif args.cmd in {"status", "dump"}:
        payload = dump_status()
        json_path, md_path = write_report("legion_ray_status_report", payload)
        print(f"[OK] Status JSON: {json_path}")
        print(f"[OK] Status MD:   {md_path}")
        print(json.dumps(payload, indent=2, default=str)[:4000])

    elif args.cmd == "register-parquet":
        payload = register_parquet(args.path, args.name)
        json_path, md_path = write_report("legion_parquet_register_report", payload)
        print(f"[OK] Registered parquet. JSON: {json_path}")
        print(f"[OK] Registered parquet. MD:   {md_path}")
        print(json.dumps(payload, indent=2, default=str)[:4000])


if __name__ == "__main__":
    main()
