import os
with open("c:/ProjectCode/stockmanager/.env", "r") as f:
    lines = f.readlines()
    for line in lines:
        if "GOOGLE_API_KEY" in line:
            parts = line.split("=")
            val = parts[1].strip() if len(parts) > 1 else "N/A"
            print(f"File Content -> Length: {len(val)}, Start: {val[:4]}, End: {val[-4:]}")
