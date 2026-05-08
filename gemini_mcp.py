#!/usr/bin/env python3
import sys
import json
import requests
import base64
import os
from dotenv import load_dotenv

# This look for the .env file and loads the variables
load_dotenv() 

# Now you fetch the variable from the environment
API_KEY = os.getenv("API_KEY")

def send_message(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()

def handle_request(req):
    method = req.get("method")
    msg_id = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        send_message({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "gemini-imagen",
                    "version": "1.0.0"
                }
            }
        })
    elif method == "tools/list":
        send_message({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "generate_image",
                        "description": "Generate an image using Nano Banana models and save it to the specified path.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "The description of the image to generate."
                                },
                                "output_path": {
                                    "type": "string",
                                    "description": "Absolute path where the image will be saved (use .jpg or .png)."
                                },
                                "model": {
                                    "type": "string",
                                    "description": "Model to use. Options: nano-banana-pro-preview, gemini-3.1-flash-image-preview, gemini-2.5-flash-image",
                                    "default": "nano-banana-pro-preview"
                                }
                            },
                            "required": ["prompt", "output_path"]
                        }
                    }
                ]
            }
        })
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        if tool_name == "generate_image":
            prompt = args.get("prompt")
            output_path = args.get("output_path")
            model = args.get("model", "nano-banana-pro-preview")
            
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
                
                data = {
                    "contents": [
                        {
                            "parts": [{"text": prompt}]
                        }
                    ]
                }
                
                resp = requests.post(url, json=data)
                resp_json = resp.json()
                
                if resp.status_code != 200:
                    error_msg = json.dumps(resp_json)
                    send_message({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [{"type": "text", "text": f"API Error: {error_msg}"}],
                            "isError": True
                        }
                    })
                    return
                
                candidates = resp_json.get("candidates", [])
                if not candidates:
                    send_message({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [{"type": "text", "text": "No candidates returned."}],
                            "isError": True
                        }
                    })
                    return
                
                parts = candidates[0].get("content", {}).get("parts", [])
                img_data = None
                for part in parts:
                    if "inlineData" in part:
                        b64_data = part["inlineData"].get("data")
                        img_data = base64.b64decode(b64_data)
                        break
                        
                if not img_data:
                    send_message({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [{"type": "text", "text": "No image data found in response."}],
                            "isError": True
                        }
                    })
                    return
                
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(img_data)
                
                send_message({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Image successfully generated and saved to {output_path}"}],
                        "isError": False
                    }
                })
            except Exception as e:
                send_message({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Exception: {str(e)}"}],
                        "isError": True
                    }
                })
        else:
            send_message({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": "Method not found"
                }
            })

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            if "method" in req:
                handle_request(req)
        except json.JSONDecodeError:
            pass

if __name__ == "__main__":
    main()
