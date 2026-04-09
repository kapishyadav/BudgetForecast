from abc import ABC, abstractmethod
import requests
import logging

logger = logging.getLogger(__name__)

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """Takes a formatted prompt and returns the AI generated text."""
        pass

# --- Concrete Implementation ---
class OllamaProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "gemma4:e2b"):
        self.url = "http://host.docker.internal:11434/api/generate"
        self.model_name = model_name

    def generate_text(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 2048}
        }
        try:
            response = requests.post(self.url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            print("--------- OLLAMA RAW RESPONSE ---------")
            print(data)
            print("---------------------------------------")
            return response.json().get('response', 'Generation failed.')
        except Exception as e:
            logger.error(f"Ollama failure: {e}")
            raise