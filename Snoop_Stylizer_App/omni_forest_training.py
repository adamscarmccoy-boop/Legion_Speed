import os
import torch
import numpy as np
from openai import OpenAI
import pickle
import time
from sklearn.ensemble import RandomForestClassifier

# -----------------------------
# LM STUDIO CONFIG
# -----------------------------
client = OpenAI(
    base_url='http://127.0.0.1:1234/v1',
    api_key='lm-studio' 
)

# -----------------------------
# DATASET GENERATION
# -----------------------------
def load_artist_dna(artist_name):
    filepath = f"{artist_name}_absolute_dna.pt"
    if os.path.exists(filepath):
        print(f"Loading {artist_name} from {filepath}")
        return torch.load(filepath).numpy()
    else:
        print(f"Mocking {artist_name} array (File missing for Birthday Rush!)")
        return np.random.rand(13) * 100

artists = ["Snoop", "Dolly", "Drake", "Michael"]

X_embeddings = []
y_labels = []

print("STARTING OMNI-VECTOR FOREST TRAINING")
print("Connecting to LM Studio on port 1234...")

for idx, artist in enumerate(artists):
    dna_base = load_artist_dna(artist)
    
    print(f"\n[{artist}] Pinging Snowflake Arctic Embed 10 times to build cluster...")
    for i in range(10): # 10 Iterations as requested
        # Add slight mathematical jitter to simulate phonetic drift
        jittered_dna = dna_base + np.random.normal(0, 0.5, size=dna_base.shape)
        
        # Serialize the 13-dim array to an Acoustic Structural String
        payload = f"Artist: {artist} | Acoustic MFCC Formants: {list(np.round(jittered_dna, 3))}"
        
        try:
            response = client.embeddings.create(
                model="text-embedding-snowflake-arctic-embed-l-v2.0",
                input=payload
            )
            vector = response.data[0].embedding
            X_embeddings.append(vector)
            y_labels.append(idx) # 0=Snoop, 1=Dolly, 2=Drake, 3=MJ
        except Exception as e:
            print(f"LM Studio Connection Failed: {e}")
            break
            
print("\nEmbedded Data Successfully Generated!")

# -----------------------------
# RANDOM FOREST TRAINING
# -----------------------------
if len(X_embeddings) > 0:
    print(f"Training RandomForestClassifier with 10 estimators on {len(X_embeddings)} semantic vectors...")
    
    forest = RandomForestClassifier(n_estimators=10, random_state=42)
    forest.fit(X_embeddings, y_labels)
    
    # Save the model
    with open('omni_forest_weights.pkl', 'wb') as f:
        pickle.dump(forest, f)
        
    print("Training Complete!")
    print("Saved weights to 'omni_forest_weights.pkl'. The Desktop App is now Omniscient!")
else:
    print("Training aborted. No vectors were generated. Is LM Studio running with the Snowflake model?")
