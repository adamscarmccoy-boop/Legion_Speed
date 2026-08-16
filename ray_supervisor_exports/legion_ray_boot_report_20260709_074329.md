# legion_ray_boot_report

Created: `2026-07-09T07:43:29`

```json
{
  "created_at": "2026-07-09T07:43:29",
  "namespace": "legion",
  "ray_initialized": true,
  "ray_address": "local",
  "actors": [
    {
      "name": "LegionSupervisor",
      "namespace": "legion",
      "state": "ok",
      "actor_type": "LegionSupervisorActor",
      "detail": "created: {\"ok\": true, \"actor\": \"LegionSupervisorActor\", \"namespace\": \"legion\", \"created_at\": \"2026-07-09T07:43:27\", \"known_actor_names\": {}}",
      "methods": [
        "list_known_actors",
        "ping",
        "remember_actor"
      ]
    },
    {
      "name": "SwarmKnowledgeRegistry",
      "namespace": "legion",
      "state": "ok",
      "actor_type": "SwarmKnowledgeRegistry/Compat",
      "detail": "created compat registry: {\"ok\": true, \"actor\": \"SwarmKnowledgeRegistryCompat\", \"created_at\": \"2026-07-09T07:43:27\", \"tables\": []}",
      "methods": [
        "dump_summary",
        "get_registered_tables_summary",
        "get_table",
        "list_tables",
        "ping",
        "register_table"
      ]
    },
    {
      "name": "SocialActor",
      "namespace": "legion",
      "state": "ok",
      "actor_type": "SocialActor",
      "detail": "created: {\"status\": \"online\", \"platforms\": {\"instagram\": \"active\", \"tiktok\": \"active\", \"spotify\": \"active\"}}",
      "methods": [
        "get_engagement_metrics",
        "ping"
      ]
    },
    {
      "name": "MarketingActor",
      "namespace": "legion",
      "state": "ok",
      "actor_type": "MarketingActor",
      "detail": "created: {\"status\": \"online\", \"engine_loaded\": true}",
      "methods": [
        "ping",
        "score_audio_dna"
      ]
    },
    {
      "name": "WardenActor",
      "namespace": "legion",
      "state": "skipped",
      "actor_type": "WardenActor",
      "detail": "needs constructor args or dependencies",
      "methods": null
    },
    {
      "name": "DSPAlignmentActor",
      "namespace": "legion",
      "state": "ok",
      "actor_type": "DSPAlignmentActor",
      "detail": "created: {\"status\": \"online\", \"db_path\": \"C:\\\\STUDIES_BACKUP\\\\vectors\\\\lancedb_store\"}",
      "methods": [
        "align_features",
        "ping"
      ]
    },
    {
      "name": "IntelligenceBridge",
      "namespace": "legion",
      "state": "skipped",
      "actor_type": "IntelligenceBridge",
      "detail": "needs constructor args or dependencies",
      "methods": null
    },
    {
      "name": "GemmaONNXAgent",
      "namespace": "legion",
      "state": "error",
      "actor_type": "GemmaONNXAgent",
      "detail": "created: The actor died because of an error raised in its creation task, \u001b[36mray::GemmaONNXAgent:GemmaONNXAgent.__init__()\u001b[39m (pid=8920, ip=127.0.0.1, actor_id=1c36c56948561fb553daaeb301000000, repr=<gemma_onnx_server.GemmaONNXAgent object at 0x00000236F2552330>)\n  File \"python\\\\ray\\\\_raylet.pyx\", line 1857, in ray._raylet.execute_task\n  File \"python\\\\ray\\\\_raylet.pyx\", line 1800, in ray._raylet.execute_task.function_executor\n  File \"E:\\WEB CASE STUDY\\.venv\\Lib\\site-packages\\ray\\_private\\function_manager.py\", line 721, in actor_method_executor\n    return method(__ray_actor, *args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"E:\\WEB CASE STUDY\\.venv\\Lib\\site-packages\\ray\\util\\tracing\\tracing_helper.py\", line 461, in _resume_span\n    return method(self, *_args, **_kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\WEB CASE STUDY\\gemma_onnx_server.py\", line 21, in __init__\n    import onnxruntime_genai as og\nModuleNotFoundError: No module named 'onnxruntime_genai'",
      "methods": [
        "generate",
        "ping"
      ]
    }
  ],
  "errors": []
}
```