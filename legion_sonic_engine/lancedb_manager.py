import os
import lancedb
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import ValidationError
from scipy.spatial.distance import euclidean

from legion_sonic_engine.utils import (
    ensure_utf8_output, SectionMetrics, MasterTrackStructuralProfile, BaselineTrackProfile
)

ensure_utf8_output()

class LanceDBManager:
    """
    Manages connections and operations for LanceDB, storing and retrieving
    audio structural profiles and baseline references.
    """
    def __init__(self, db_path: str, table_name: str):
        self.db_path = db_path
        self.table_name = table_name
        self.db: Optional[lancedb.LanceDB] = None
        self.table: Optional[lancedb.table.Table] = None
        print(f"🗄️ LanceDBManager initialized for path: {db_path} | Table: {table_name}")

    def connect(self):
        """Establishes connection to LanceDB."""
        try:
            self.db = lancedb.connect(self.db_path)
            print(f"✅ Connected to LanceDB at {self.db_path}")
        except Exception as e:
            print(f"❌ Failed to connect to LanceDB: {e}")
            raise

    def create_table_if_not_exists(self):
        """
        Creates the LanceDB table with the defined schema if it doesn't exist.
        The schema is inferred from the Pydantic model's first data ingestion.
        We'll use a placeholder for the vector field for initial table creation.
        """
        if not self.db:
            self.connect()
        
        # LanceDB schema is inferred from the first insertion.
        # We need a dummy record that matches the BaselineTrackProfile structure
        # to ensure the 'vector' field is created correctly.
        dummy_segment = SectionMetrics(
            segment_name="dummy", start_time_sec=0.0, end_time_sec=1.0, duration_sec=1.0,
            rms_db=-23.0, crest_factor=1.0, integrated_lufs=-23.0, loudness_range_lra=5.0,
            sub_bass_energy=0.0, bass_energy=0.0, mid_energy=0.0, high_energy=0.0,
            spectral_centroid=2000.0, mfcc_embedding=[0.0]*128
        )
        dummy_profile = BaselineTrackProfile(
            track_name="dummy_init", original_filepath="/dummy/path.wav",
            vector=[0.0]*128, # Ensure vector field is present
            segment_data=[dummy_segment]
        )
        
        try:
            # Try to open, if it fails, create
            self.table = self.db.open_table(self.table_name)
            print(f"📖 Opened existing LanceDB table: {self.table_name}")
        except lancedb.exceptions.TableNotFound:
            # If the table doesn't exist, create it with the dummy record.
            # LanceDB will infer the schema from this first record.
            # Remove the dummy later or simply tolerate it for schema bootstrapping.
            print(f"✨ Creating new LanceDB table: {self.table_name}")
            self.table = self.db.create_table(self.table_name, data=[dummy_profile.model_dump()])
            # It's good practice to remove the dummy record after creation
            self.table.delete(f"track_name = 'dummy_init'")
            print(f"✅ New LanceDB table '{self.table_name}' created.")
        except Exception as e:
            print(f"❌ Error creating/opening LanceDB table: {e}")
            raise

    def add_baseline_profile(self, profile_data: MasterTrackStructuralProfile, track_name: str):
        """
        Adds a MasterTrackStructuralProfile as a baseline to LanceDB.
        Calculates a track-level MFCC embedding for similarity search.
        
        Args:
            profile_data: The MasterTrackStructuralProfile to add.
            track_name: A unique name to identify this baseline.
        """
        if not self.table:
            self.create_table_if_not_exists()
        
        # Check for existing baseline with the same name
        if len(self.table.search().where(f"track_name = '{track_name}'").limit(1).to_list()) > 0:
            print(f"⚠️ Baseline '{track_name}' already exists. Skipping addition.")
            return

        # Generate a pooled MFCC vector for the entire track from its segments
        # This will be the main vector for track-level similarity search
        all_mfccs = [seg.mfcc_embedding for seg in profile_data.segment_data if seg.mfcc_embedding]
        if not all_mfccs:
            print(f"❌ No MFCC embeddings found in profile for '{track_name}'. Cannot add baseline.")
            return
        
        track_embedding = np.mean(all_mfccs, axis=0).tolist()
        
        try:
            baseline_entry = BaselineTrackProfile(
                track_name=track_name,
                original_filepath=profile_data.original_filepath,
                vector=track_embedding,
                segment_data=profile_data.segment_data
            )
            self.table.add([baseline_entry.model_dump()])
            print(f"✅ Baseline '{track_name}' successfully added to LanceDB.")
        except ValidationError as e:
            print(f"❌ Pydantic validation error adding baseline '{track_name}': {e}")
        except Exception as e:
            print(f"❌ Error adding baseline '{track_name}' to LanceDB: {e}")

    def query_closest_baselines(self, query_mfcc_embedding: List[float], n_results: int = 1) -> List[Dict[str, Any]]:
        """
        Queries LanceDB for the closest baseline tracks based on MFCC embedding.
        
        Args:
            query_mfcc_embedding: The MFCC embedding of the track to query.
            n_results: Number of closest baselines to return.
        
        Returns:
            A list of dictionaries, each representing a matched baseline track.
        """
        if not self.table:
            self.create_table_if_not_exists()
        
        try:
            # LanceDB performs vector similarity search
            results = self.table.search(query_mfcc_embedding).limit(n_results).to_list()
            print(f"🔍 Found {len(results)} closest baselines.")
            return results
        except Exception as e:
            print(f"❌ Error querying LanceDB: {e}")
            return []
            
    def get_baseline_by_name(self, track_name: str) -> Optional[BaselineTrackProfile]:
        """
        Retrieves a specific baseline track profile by its name.
        """
        if not self.table:
            self.create_table_if_not_exists()

        try:
            results = self.table.search().where(f"track_name = '{track_name}'").limit(1).to_list()
            if results:
                return BaselineTrackProfile(**results[0])
            else:
                return None
        except Exception as e:
            print(f"❌ Error retrieving baseline '{track_name}': {e}")
            return None

# Example usage (for local testing of the manager)
# if __name__ == "__main__":
#     DB_PATH = "C:\\STUDIES_BACKUP\\vectors\\lancedb_omni_snowflake_rag" # Update your path
#     TABLE_NAME = "sonic_engine_baselines"

#     manager = LanceDBManager(DB_PATH, TABLE_NAME)
#     manager.connect()
#     manager.create_table_if_not_exists()

#     # Dummy profile to add for testing
#     dummy_segment_metrics = SectionMetrics(
#         segment_name="Intro", start_time_sec=0.0, end_time_sec=10.0, duration_sec=10.0,
#         rms_db=-18.0, crest_factor=4.5, integrated_lufs=-20.0, loudness_range_lra=6.0,
#         sub_bass_energy=100.0, bass_energy=500.0, mid_energy=1000.0, high_energy=200.0,
#         spectral_centroid=2500.0, mfcc_embedding=[float(i % 100) / 100.0 for i in range(128)]
#     )
#     dummy_profile_data = MasterTrackStructuralProfile(
#         filename="dummy_test_track.wav", original_filepath="/tmp/dummy_test_track.wav",
#         total_sections_found=1, processing_time_ms=500.0, segment_data=[dummy_segment_metrics]
#     )

#     test_track_name = "Dummy Baseline Track 1"
#     manager.add_baseline_profile(dummy_profile_data, test_track_name)

#     # Query for a similar track
#     query_embedding = [float((i + 5) % 100) / 100.0 for i in range(128)] # Slightly different embedding
#     closest = manager.query_closest_baselines(query_embedding, n_results=1)
#     if closest:
#         print(f"\nClosest baseline found: {closest[0]['track_name']}")
#         print(f"  Segment Data sample: {closest[0]['segment_data'][0]['segment_name']}")
#     else:
#         print("No baselines found.")
