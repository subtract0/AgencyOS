from dataclasses import dataclass
import os

@dataclass
class ModelProfile:
    name: str
    api_base: str
    api_key: str = "not-needed"
    max_tokens: int = 2000

# The Split-Brain Configuration
# Based on MODEL_STRATEGY_LOCAL_FIRST_2025-12.md

MODELS = {
    # THE FAST BRAIN (Tools, Routing, Voice)
    # Model: Fallback to Qwen (8082) due to Nemotron-9B Instability
    "nemotron": ModelProfile(
        name="mlx-community/Qwen2.5-Coder-32B-Instruct-4bit",
        api_base="http://127.0.0.1:8082/v1",
        max_tokens=8192
    ),

    # THE DEEP BRAIN (Coding, Planning, Legacy)
    # Model: Qwen2.5-Coder-32B
    "deep_coder": ModelProfile(
        name="mlx-community/Qwen2.5-Coder-32B-Instruct-4bit",
        api_base="http://127.0.0.1:8082/v1",
        max_tokens=8192
    ),

    # THE EYE (Vision, Meaning, Verification)
    # Model: Qwen2.5-VL-7B-Instruct
    "qwen_vl": ModelProfile(
        name="mlx-community/Qwen2.5-VL-7B-Instruct-4bit",
        api_base="http://127.0.0.1:8084/v1",
        max_tokens=4096
    ),
    
    # OFFLINE SAFETY
    "offline": ModelProfile(
        name="offline-guard",
        api_base="http://127.0.0.1:11434/v1", # fallback to Ollama if needed
        max_tokens=1024
    ),

    # THE EMPATH (Psychology, Semantics, Suffering Analysis)
    # Model: Llama-3.3-70B-Instruct (High EQ, 128GB RAM optimized)
    "empath": ModelProfile(
        name="mlx-community/Llama-3.3-70B-Instruct-4bit",
        api_base="http://127.0.0.1:8086/v1",
        max_tokens=4096
    )
}

def get_model_config(profile_name: str):
    """Returns the ModelProfile for a given key."""
    return MODELS.get(profile_name, MODELS["deep_coder"])
