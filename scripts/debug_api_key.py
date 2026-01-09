import os
import google.generativeai as genai
from dotenv import load_dotenv

# Try to load .env from multiple possible locations
# Try to load .env from multiple possible locations with override
load_dotenv(".env", override=True)
load_dotenv("../../.env", override=True)
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"), override=True)

api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY NOT found in environment.")
    exit(1)

print(f"Key loaded! Length: {len(api_key)}")
print(f"Key starts with: {api_key[:4]}...")

try:
    genai.configure(api_key=api_key)
    print("\nAttempting to list models with this key...")
    models = genai.list_models()
    count = 0
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            count += 1
    if count == 0:
        print("No models supported for generateContent found.")
except Exception as e:
    print(f"\nAPI Error: {e}")
