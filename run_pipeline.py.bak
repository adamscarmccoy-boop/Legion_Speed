import os
import time
import json
import ray
import polars as pl
import pyarrow as pa
import logging
import sys

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


# CONFIGURATION
INPUT_PARQUET = 'C:/WEB CASE STUDY/ray_categories.parquet'
OUTPUT_TRAINING_DIR = 'C:/WEB CASE STUDY/training_latents'

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('pipeline_errors.log'), logging.StreamHandler()]
)
logger = logging.getLogger('AAFLOW')

try:
    import sonic_dsp
    HAS_CPP = True
    logger.info('C++ DSP Engine loaded successfully.')
except ImportError:
    HAS_CPP = False
    logger.warning('C++ DSP Engine not found. Using Python fallback.')

os.environ['POLARS_MAX_THREADS'] = '1'

if not ray.is_initialized():
    logger.info('Booting Ray Cluster on 12 Local CPUs...')
    ray.init(num_cpus=12, ignore_reinit_error=True)

@ray.remote(num_cpus=1)
class DiffusionDatasetWorker:
    def process_audio_batch(self, arrow_batch):
        try:
            if HAS_CPP:
                return sonic_dsp.process_audio_chunk(arrow_batch)
            else:
                df = pl.from_arrow(arrow_batch)
                res_df = df.with_columns(
                    action=pl.lit('PROCESSED_PY'),
                    latent_path=pl.col('path') + '_latent.npy'
                )
                return res_df.to_arrow()
        except Exception as e:
            logger.error(f'Worker error: {e}')
            return None

class TrainingDataOrchestrator:
    def __init__(self):
        self.workers = [DiffusionDatasetWorker.remote() for _ in range(12)]

    def build_dataset(self, df: pl.DataFrame):
        if df.height == 0:
            logger.error('Input DataFrame is empty.')
            return None

        arrow_table = df.to_arrow()
        batch_size = 500 
        total_rows = arrow_table.num_rows
        
        batches = [arrow_table.slice(i, length=batch_size) for i in range(0, total_rows, batch_size)]
        logger.info(f'Dispatching {len(batches)} batches across 12 CPUs...')

        processing_futures = []
        for i, batch in enumerate(batches):
            worker = self.workers[i % 12]
            batch_ref = ray.put(batch) 
            processing_futures.append(worker.process_audio_batch.remote(batch_ref))

        finished_tables = []
        while processing_futures:
            done_refs, processing_futures = ray.wait(processing_futures, num_returns=1)
            for done_ref in done_refs:
                try:
                    res = ray.get(done_ref)
                    if res is not None:
                        finished_tables.append(res)
                except Exception as e:
                    logger.error(f'Error retrieving result: {e}')
                
        if not finished_tables:
            return None

        combined_arrow = pa.concat_tables(finished_tables)
        return pl.from_arrow(combined_arrow)

if __name__ == '__main__':
    try:
        logger.info(f'Loading index from {INPUT_PARQUET}...')
        raw_inventory = pl.read_parquet(INPUT_PARQUET)
        logger.info(f'Loaded {raw_inventory.height} samples from parquet.')
    except Exception as e:
        logger.error(f'Failed to read parquet: {e}')
        exit(1)

    orchestrator = TrainingDataOrchestrator()
    
    start_time = time.time()
    try:
        final_training_set = orchestrator.build_dataset(raw_inventory)
        
        if final_training_set is not None:
            os.makedirs(OUTPUT_TRAINING_DIR, exist_ok=True)
            output_path = os.path.join(OUTPUT_TRAINING_DIR, 'training_index.parquet')
            final_training_set.write_parquet(output_path)
            
            end_time = time.time()
            logger.info('LOCAL ZERO-COPY TRAINING SET COMPLETE')
            logger.info(f'Processed {len(raw_inventory)} files in {end_time - start_time:.4f} seconds.')
            print(final_training_set.head())
        else:
            logger.error('Pipeline failed to produce a result set.')
            
    except Exception as e:
        logger.error(f'Unexpected pipeline failure: {e}')