import torch
import numpy as np

router = torch.load(
    r"C:\WEB CASE STUDY\Snoop_Stylizer_App\Snoop_segment_router.pt",
    map_location="cpu",
    weights_only=False
)

profile = torch.load(
    r"C:\WEB CASE STUDY\Snoop_Stylizer_App\Snoop_segment_profile.pt",
    map_location="cpu",
    weights_only=False
)

model = torch.nn.Sequential(
    torch.nn.Linear(57, 128),
    torch.nn.ReLU(),
    torch.nn.Linear(128, 64),
    torch.nn.ReLU(),
    torch.nn.Linear(64, 12)
)

model.load_state_dict(router["model_state_dict"])
model.eval()

x = np.cumsum(np.random.randn(30, 57) * 0.05, axis=0).astype(np.float32)

with torch.no_grad():
    logits = model(torch.tensor(x))
    clusters = torch.argmax(logits, dim=1).numpy()

print("Clusters:")
print(clusters)

print("\nProfile keys:")
print(profile.keys())

print("\nCentroid shape:")
print(np.array(profile["cluster_centroids"]).shape)