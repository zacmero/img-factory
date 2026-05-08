#!/usr/bin/env python3
import sys
import json
import requests
import base64
import os
import argparse
def load_env_fallback():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    key = parts[0].strip()
                    value = parts[1].strip()
                    # Strip quotes if present
                    value = value.strip("'").strip('"')
                    os.environ[key] = value

# Try to use dotenv, fallback to manual parse if not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    load_env_fallback()

# Now you fetch the variable from the environment
API_KEY = os.getenv("API_KEY")

def main():
    parser = argparse.ArgumentParser(description="Generate an image using Gemini models")
    parser.add_argument("--prompt", type=str, required=True, help="Image prompt")
    parser.add_argument("--output", type=str, required=True, help="Output file path (e.g., image.png or image.jpg)")
    parser.add_argument("--model", type=str, default="nano-banana-pro-preview", help="Model name (e.g., nano-banana-pro-preview)")
    
    args = parser.parse_args()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{args.model}:generateContent?key={API_KEY}"
    data = {
        "contents": [
            {
                "parts": [{"text": args.prompt}]
            }
        ]
    }
    
    print(f"Generating image with prompt: {args.prompt} using model {args.model} ...")
    resp = requests.post(url, json=data)
    
    if resp.status_code != 200:
        print(f"Error: {resp.text}", file=sys.stderr)
        sys.exit(1)
        
    resp_json = resp.json()
    candidates = resp_json.get("candidates", [])
    if not candidates:
        print("Error: No candidates returned.", file=sys.stderr)
        sys.exit(1)
        
    parts = candidates[0].get("content", {}).get("parts", [])
    
    img_data = None
    for part in parts:
        if "inlineData" in part:
            b64_data = part["inlineData"].get("data")
            img_data = base64.b64decode(b64_data)
            break
            
    if not img_data:
        print("Error: No image data found in response.", file=sys.stderr)
        sys.exit(1)
    
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "wb") as f:
        f.write(img_data)
        
    print(f"Success! Image saved to {args.output}")

if __name__ == "__main__":
    main()
