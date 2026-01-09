import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

print(f"Using API Key: {api_key[:10]}...")

print("\n--- Listing Models ---")
try:
    models = genai.list_models()
    for m in models:
        methods = ", ".join(m.supported_generation_methods)
        print(f"Name: {m.name} | Methods: {methods}")
except Exception as e:
    print(f"Error listing models: {e}")
