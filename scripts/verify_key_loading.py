import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env")
else:
    print(f"Key Found! Length: {len(api_key)}")
    print(f"Key starts with: {api_key[:4]}...")
    print(f"Key ends with: ...{api_key[-4:]}")
