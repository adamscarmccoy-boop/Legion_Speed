# main_app.py

import ray
from ray import PlacementGroupID as pg
import ray.util.queue
import os
import logging
import time
import uuid
from typing import List, Dict, Any, Optional

from request_dispatcher import submit_inference_request
import model_actor
import my_model_loader

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
    # Avoid raising SystemExit inside an atexit callback (which causes RuntimeWarnings)
    if args and isinstance(args[0], int):
        sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


# --- Configuration ---
NUM_PHYSICAL_GPUS = 4        # Adjust this to match the actual number of GPUs on your Windows machine
MODEL_NAME = "audiocraft-large"  # Example model identifier
GLOBAL_REQUEST_QUEUE_CAPACITY = 100
GLOBAL_RESULT_QUEUE_CAPACITY = 100

# Configure logging for the entire application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_ray_environment(num_gpus: int) -> pg.PlacementGroup:
    """
    Initializes Ray and sets up a single placement group with bundles
    for each GPU. Each bundle requests 1 GPU and 1 CPU.
    """
    logger.info(f"Initializing Ray with {num_gpus} GPUs...")

    # Ensure Ray is not already initialized, or shut it down cleanly if it is.
    if ray.is_initialized():
        logger.warning("Ray is already initialized. Shutting down existing instance.")
        ray.shutdown()
    
    # Initialize Ray. logs are directed to stderr for cleaner stdout.
    ray.init(log_to_stdout=False, log_to_stderr=True) 

    # Define a bundle for each GPU (1 CPU per GPU to run the actor logic)
    bundles = [{"GPU": 1, "CPU": 1} for _ in range(num_gpus)]
    
    # Create a single placement group that requests all bundles.
    # STRICT_PACK ensures that resources within each bundle are allocated on a single node (if possible).
    # Since we're assuming a single machine, this just means all requested bundles will be fulfilled.
    all_gpus_pg = pg.placement_group(
        bundles=bundles,
        strategy="STRICT_PACK"
    )
    # Wait for the placement group to be ready and all bundles allocated
    ray.get(all_gpus_pg.ready())

    logger.info(f"Ray initialized and placement group '{all_gpus_pg.id.hex()}' with {num_gpus} GPU bundles created.")
    return all_gpus_pg

def launch_model_actors(
    global_pg: pg.PlacementGroup,
    request_queue: ray.util.queue.Queue,
    result_queue: ray.util.queue.Queue
) -> List[ray.actor.ActorHandle]:
    """
    Launches a ModelServingActor for each GPU bundle within the global placement group.
    Each actor is explicitly bound to one specific GPU bundle.
    """
    actors: List[ray.actor.ActorHandle] = []
    
    # Iterate through the number of physical GPUs to launch actors
    for i in range(NUM_PHYSICAL_GPUS):
        try:
            # Bind each actor to a specific bundle within the global placement group.
            # `placement_group_bundle_index=i` ensures this actor gets the i-th bundle.
            actor = model_actor.ModelServingActor.options(
                name=f"{MODEL_NAME}_server_actor_{i}",
                num_gpus=1, # Request 1 GPU for the actor, Ray maps this to the assigned bundle's GPU
                placement_group=global_pg,
                placement_group_bundle_index=i,
                max_concurrency=1 # Ensures only one task runs at a time within the actor
            ).remote(gpu_id_logical=i, model_name=MODEL_NAME)
            
            actors.append(actor)
            logger.info(f"Launched ModelServingActor '{actor._ray_actor_id.hex()}' (logical ID: {i}) bound to bundle index {i}.")
            
            # Start the micro-batch worker task on this actor.
            # The .remote() call ensures this worker runs asynchronously within the actor's context.
            actor.start_micro_batch_worker.remote(request_queue, result_queue)
            logger.info(f"Started micro-batch worker for actor logical ID {i}.")
        except Exception as e:
            logger.error(f"Failed to launch ModelServingActor or its worker for bundle index {i}: {e}", exc_info=True)
            # Depending on requirements, might want to exit or try to recover here.
            # For now, we'll continue, but this actor won't be in the 'actors' list.
    return actors

def main():
    # 1. Initialize Ray and create placement groups
    global_pg = setup_ray_environment(NUM_PHYSICAL_GPUS)
    
    # 2. Create global queues
    # These queues are Ray objects, accessible by actors across the Ray cluster.
    request_queue = ray.util.queue.Queue(maxsize=GLOBAL_REQUEST_QUEUE_CAPACITY, name="request_queue")
    result_queue = ray.util.queue.Queue(maxsize=GLOBAL_RESULT_QUEUE_CAPACITY, name="result_queue")
    logger.info(f"Global Request Queue capacity: {GLOBAL_REQUEST_QUEUE_CAPACITY}")
    logger.info(f"Global Result Queue capacity: {GLOBAL_RESULT_QUEUE_CAPACITY}")
    
    # 3. Launch model actors bound to GPUs
    # This also starts their micro-batch workers.
    actors = launch_model_actors(global_pg, request_queue, result_queue)
    if not actors:
        logger.error("No model actors were launched successfully. Exiting.")
        if ray.is_initialized():
            ray.shutdown()
        return

    # 4. Example client interaction (simulates submitting inference requests)
    logger.info("\nSubmitting example inference requests...")
    submitted_request_ids: List[str] = []
    num_requests_to_submit = 5
    for i in range(num_requests_to_submit):
        prompt = f"A high-quality audio clip of a cat purring and a dog barking. Request {i+1}."
        # submit_inference_request now explicitly returns the request_id or None
        request_id = submit_inference_request(request_queue, prompt)
        if request_id:
            submitted_request_ids.append(request_id)
        else:
            logger.warning(f"Failed to submit request {i+1} for prompt: '{prompt[:50]}...'")
        time.sleep(0.2)  # Simulate a slight delay between submissions

    logger.info(f"\nSubmitted {len(submitted_request_ids)} example requests. Waiting for results...")
    
    # 5. Retrieve results (simplified demo)
    # This loop tries to fetch as many results as were successfully submitted.
    results_received = 0
    while results_received < len(submitted_request_ids):
        try:
            # Block until a result is available, with a timeout.
            result: Dict[str, Any] = result_queue.get(timeout=30)
            results_received += 1
            log_message = (
                f"Received result {results_received}/{len(submitted_request_ids)}: "
                f"request_id={result.get('request_id', 'N/A')}, "
                f"status={result.get('status', 'N/A')}, "
                f"prompt='{result.get('prompt', 'N/A')[:30]}...' "
            )
            if result.get('status') == 'error':
                logger.error(log_message + f" Error: {result.get('output', {}).get('error', 'Unknown error')}")
            elif result.get('status') == 'cpu':
                 logger.warning(log_message + "(CPU Fallback)")
            else:
                logger.info(log_message)
        except ray.exceptions.GetTimeoutError:
            logger.error(f"Timeout (30s) waiting for results. Received {results_received}/{len(submitted_request_ids)} so far. Some results may be pending or lost.")
            break # Exit if we timeout on getting results
        except Exception as e:
            logger.error(f"Unexpected error fetching result: {e}", exc_info=True)
            break # Exit on unexpected error

    # Keep the application running indefinitely after demo (or Ctrl+C to exit)
    logger.info("\nDemo complete. Application running. Press Ctrl+C to shut down.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down Ray application.")
    
    finally:
        # Ensure Ray is shut down cleanly when the application exits.
        if ray.is_initialized():
            ray.shutdown()
            logger.info("Ray shut down successfully.")

if __name__ == "__main__":
    main()