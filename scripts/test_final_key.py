import os
import google.generativeai as genai
from dotenv import load_dotenv

# Path to .env
root_dir = "c:/ProjectCode/stockmanager"
env_path = os.path.join(root_dir, ".env")

# Load and check
load_dotenv(env_path, override=True)
api_key = os.environ.get("GOOGLE_API_KEY")

print(f"DEBUG: Key length: {len(api_key) if api_key else 'None'}")
if api_key:
    # Print key with markers to see hidden spaces
    print(f"DEBUG: Key value -> |{api_key}|")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Tiny test call
        response = model.generate_content("hi")
        print("SUCCESS: Gemini responded!")
    except Exception as e:
        print(f"FAILURE: {e}")
else:
    print("FAILURE: No API key found")
