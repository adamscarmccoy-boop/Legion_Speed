from huggingface_hub import whoami
try:
    user = whoami()
    print(f"Authenticated as: {user}")
except Exception as e:
    print(f"Authentication failed: {e}")
