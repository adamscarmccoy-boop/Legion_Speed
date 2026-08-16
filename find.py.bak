import ray

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


def audit_legion_swarm():
    try:
        # Connect to your existing cluster
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print(f"🟢 Legion Cluster: LIVE (Dashboard: http://127.0.0.1:8265)")

        # 1. Get all named actors
        all_actors = ray.util.list_named_actors(all_namespaces=True)
        legion_actors = [a for a in all_actors if a.get('namespace') == 'legion']
        
        print(f"\n--- [ FLEET STATUS: {len(legion_actors)} Actors ] ---")
        for actor in legion_actors:
            name = actor.get('name', 'Unnamed')
            state = actor.get('state', 'ALIVE') # Safe fallback
            print(f"• {name: <25} | State: {state}")

        # 2. Inventory Check (Peeking into Shards)
        registries = {
            "swarm_reg": "get_all_tables",
            "code_reg": "get_all_shards",
            "SwarmKnowledgeRegistry": "get_all_tables" # Matches your live actor name
        }

        for actor_name, method_name in registries.items():
            try:
                handle = ray.get_actor(actor_name, namespace="legion")
                # Call the inventory method dynamically
                inventory = ray.get(getattr(handle, method_name).remote())
                
                print(f"\n--- [ INVENTORY: {actor_name} ] ---")
                if not inventory:
                    print("  (Registry is empty - No shards mapped yet)")
                else:
                    print(f"  Total Mapped: {len(inventory)} items")
                    for key in inventory.keys():
                        print(f"  └─ {key}")
            except (ValueError, AttributeError):
                # Actor not found or method doesn't exist yet
                continue

    except Exception as e:
        print(f"❌ Audit Failed: {e}")
        print("Tip: Ensure you have updated the Actors in your main script to include 'get_all' methods.")

if __name__ == "__main__":
    audit_legion_swarm()