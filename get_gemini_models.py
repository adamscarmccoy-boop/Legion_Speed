import requests
import json

key = "AQ.Ab8RN6KJExte7emxXRqeM3XFYe-5HFtwghi77sqTgm4jEGvoyA"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
try:
    response = requests.get(url)
    with open("gemini_models.json", "w") as f:
        f.write(response.text)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
