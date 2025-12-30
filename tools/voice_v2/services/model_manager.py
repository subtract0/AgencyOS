
import logging
from typing import Dict, Optional, Any
from mlx_lm import load, generate

class ModelManager:
    """
    Manages multiple MLX models in memory.
    Designed for 128GB Unified Memory systems where multiple large models 
    can coexist without swapping.
    """
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.tokenizers: Dict[str, Any] = {}
        self.lock = False # specialized lock if needed
        
    def load_model(self, model_id: str, alias: str):
        """Loads a model into memory if not already present."""
        if alias in self.models:
            logging.info(f"ModelManager: {alias} already loaded.")
            return

        logging.info(f"ModelManager: Loading {alias} ({model_id})...")
        try:
            model, tokenizer = load(model_id)
            self.models[alias] = model
            self.tokenizers[alias] = tokenizer
            logging.info(f"ModelManager: {alias} loaded successfully.")
        except Exception as e:
            logging.error(f"ModelManager: Failed to load {alias}: {e}")
            raise

    def get_model(self, alias: str):
        return self.models.get(alias), self.tokenizers.get(alias)

    def generate_response(self, alias: str, prompt: str, **kwargs) -> str:
        model, tokenizer = self.get_model(alias)
        if not model:
            raise ValueError(f"Model alias '{alias}' not found.")
        
        logging.info(f"ModelManager: Generating with {alias}...")
        return generate(model, tokenizer, prompt=prompt, verbose=False, **kwargs)

# Global singleton? Or instantiated in AgencyLLMService?
# Better to have it as a singleton or shared instance.
