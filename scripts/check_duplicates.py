import os
with open("c:/ProjectCode/stockmanager/.env", "r") as f:
    lines = f.readlines()
    count = 0
    for i, line in enumerate(lines):
        if "GOOGLE_API_KEY" in line:
            count += 1
            print(f"Line {i+1}: Found GOOGLE_API_KEY")
    print(f"Total entries: {count}")
