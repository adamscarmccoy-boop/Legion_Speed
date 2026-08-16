# legion_ray_status_report

Created: `2026-07-24T10:46:24`

```json
{
  "created_at": "2026-07-24T10:46:24",
  "namespace": "legion",
  "actors": {
    "LegionSupervisor": {
      "state": "missing",
      "error": "Failed to look up actor with name 'LegionSupervisor'. This could because 1. You are trying to look up a named actor you didn't create. 2. The named actor died. 3. You did not use a namespace matching the namespace of the actor."
    },
    "SwarmKnowledgeRegistry": {
      "state": "ok",
      "detail": "No ping() method; actor handle exists.",
      "methods": [
        "add_knowledge_batch",
        "get_registered_tables_summary",
        "get_table",
        "get_table_ref",
        "register_table",
        "table_count"
      ],
      "get_registered_tables_summary": {}
    },
    "SocialActor": {
      "state": "missing",
      "error": "Failed to look up actor with name 'SocialActor'. This could because 1. You are trying to look up a named actor you didn't create. 2. The named actor died. 3. You did not use a namespace matching the namespace of the actor."
    },
    "MarketingActor": {
      "state": "missing",
      "error": "Failed to look up actor with name 'MarketingActor'. This could because 1. You are trying to look up a named actor you didn't create. 2. The named actor died. 3. You did not use a namespace matching the namespace of the actor."
    },
    "WardenActor": {
      "state": "missing",
      "error": "Failed to look up actor with name 'WardenActor'. This could because 1. You are trying to look up a named actor you didn't create. 2. The named actor died. 3. You did not use a namespace matching the namespace of the actor."
    },
    "DSPAlignmentActor": {
      "state": "missing",
      "error": "Failed to look up actor with name 'DSPAlignmentActor'. This could because 1. You are trying to look up a named actor you didn't create. 2. The named actor died. 3. You did not use a namespace matching the namespace of the actor."
    },
    "IntelligenceBridge": {
      "state": "missing",
      "error": "Failed to look up actor with name 'IntelligenceBridge'. This could because 1. You are trying to look up a named actor you didn't create. 2. The named actor died. 3. You did not use a namespace matching the namespace of the actor."
    }
  }
}
```