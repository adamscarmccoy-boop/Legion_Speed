import os
import numpy as np
import torch
import json
from sonic_to_visual_bridge import SonicToVisualBridgeActor

def run_logic_tests():
    print("Starting Sovereign Bridge Logic Validation (Non-Ray Mode)...\n")
    
    # 1. Instantiate Actor as a standard class (bypassing Ray remote)
    print("Testing Class Initialization...")
    try:
        # We instantiate the class directly. 
        # Since it's decorated with @ray.remote, the class itself 
        # is actually a RemoteFunction/Actor wrapper. 
        # To test the logic, we access the underlying class via ._class_
        # or we can just test the methods if we had a non-remote version.
        # Given the current code, the most reliable way to test the logic 
        # without Ray is to instantiate the class using the __init__ 
        # logic directly or a mock.
        
        # For this test, we'll use a simple trick: 
        # Since the logic is in the class, we can just test it as a regular class
        # by ignoring the decorator for a moment in our test.
        
        # In the actual file, the class is decorated. 
        # We can use the class's underlying implementation:
        BridgeClass = SonicToVisualBridgeActor._class_ if hasattr(SonicToVisualBridgeActor, '_class_') else SonicToVisualBridgeActor
        
        actor = BridgeClass()
        print("✅ Logic Class initialized successfully.")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return

    # 2. Test Valid Input
    print("\nTesting Valid DNA Vector (Dim=41)...")
    valid_dna = np.random.rand(41).astype(np.float32)
    try:
        result = actor.bridge_dna_to_prompt(valid_dna)
        print(f"✅ Success! Prompt generated: {result.llm_expanded_prompt[:100]}...")
    except Exception as e:
        print(f"❌ Valid input failed: {e}")

    # 3. Test Invalid Input (Too Short)
    print("\nTesting Invalid DNA Vector (Dim=10)...")
    invalid_dna = np.random.rand(10).astype(np.float32)
    try:
        actor.bridge_dna_to_prompt(invalid_dna)
        print("❌ Failed: Actor should have raised a ValueError for short vector.")
    except Exception as e:
        if "Invalid DNA vector shape" in str(e):
            print(f"✅ Success: Correctly caught invalid shape. Error: {e}")
        else:
            print(f"❌ Caught unexpected error: {e}")

    # 4. Test None Input
    print("\nTesting None Input...")
    try:
        actor.bridge_dna_to_prompt(None)
        print("❌ Failed: Actor should have raised a ValueError for None input.")
    except Exception as e:
        if "Invalid DNA vector shape" in str(e):
            print(f"✅ Success: Correctly caught None input. Error: {e}")
        else:
            print(f"❌ Caught unexpected error: {e}")

    print("\nLogic Validation Suite Complete.")

if __name__ == "__main__":
    run_logic_tests()
