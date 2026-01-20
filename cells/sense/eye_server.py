
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
import mlx_vlm
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config
import base64
import tempfile

app = FastAPI()

MODEL_PATH = "mlx-community/Qwen2.5-VL-7B-Instruct-4bit"
PORT = 8084

print(f"👁️ Loading The Eye ({MODEL_PATH})...")
model, processor = load(MODEL_PATH)
config = load_config(MODEL_PATH)
print("👁️ The Eye is Open.")

class MessageContent(BaseModel):
    type: str
    text: Optional[str] = None
    image_url: Optional[Dict[str, str]] = None

class Message(BaseModel):
    role: str
    content: Union[str, List[MessageContent]]

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.7

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    try:
        # 1. Parse Messages & Images
        # mlx_vlm.apply_chat_template expects a specific format or we construct prompt manually
        # For Qwen2-VL, we strictly follow the processor's chat template if available
        
        # We need to extract images and save them to temp files because apply_chat_template often expects paths
        # OR we check if processor supports PIL images directly.
        
        formatted_messages = []
        temp_files = [] 
        
        for msg in request.messages:
            if isinstance(msg.content, str):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                # Handle List[MessageContent]
                new_content = []
                for item in msg.content:
                    if item.type == "text":
                        new_content.append({"type": "text", "text": item.text})
                    elif item.type == "image_url":
                        # Decode Base64
                        url = item.image_url["url"]
                        if url.startswith("data:image"):
                            header, encoded = url.split(",", 1)
                            data = base64.b64decode(encoded)
                            
                            # Create temp file
                            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                            tf.write(data)
                            tf.close()
                            temp_files.append(tf.name)
                            
                            new_content.append({"type": "image", "image": tf.name})
                        else:
                            # Assume path or remote url
                            new_content.append({"type": "image", "image": url})
                
                formatted_messages.append({"role": msg.role, "content": new_content})

        # 2. Apply Template
        prompt = apply_chat_template(processor, config, formatted_messages)
        
        # 3. Generate
        # mlx_vlm.generate takes (model, processor, prompt, images, ...)
        # We need to pass the list of images corresponding to the prompt
        # Actually, apply_chat_template for Qwen-VL handles the <image> token insertion
        # But `generate` usually needs the processed images.
        
        # For Qwen2-VL in mlx_vlm, usage is:
        # output = generate(model, processor, prompt, verbose=False) 
        # Wait, apply_chat_template returns a string prompt. 
        # How does it handle images? 
        # We might need to use `processor(images=..., text=...)`.
        
        # Let's use the high-level `generate` function from mlx_vlm which handles image loading from prompt?
        # No, `generate` signature: (model, processor, prompt, images=None, ...)
        # We need to pass the list of image paths/objects.
        
        # Collect all image paths from the formatted_messages
        batch_images = []
        if temp_files:
             batch_images = temp_files
        
        text_output = generate(
            model, 
            processor, 
            prompt, 
            images=batch_images if batch_images else None,
            max_tokens=request.max_tokens, 
            verbose=True
        )

        # Cleanup
        for f in temp_files:
            os.remove(f)

        return {
            "id": "chatcmpl-eye",
            "object": "chat.completion",
            "created": 12345678,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": text_output
                },
                "finish_reason": "stop"
            }]
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
