"""Core LLM integration for Orby Coder."""
import requests
import json
from typing import Generator, Dict, Any, Optional
from pathlib import Path
import ollama
from openai import OpenAI
from orby_coder.config.config_manager import ModelConfig

class LocalLLMProvider:
    """Handles communication with local LLM backends."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = None
        
        if config.backend == "lmstudio":
            # LM Studio uses OpenAI-compatible API
            self.client = OpenAI(base_url=config.lmstudio_base_url, api_key="dummy")
        # For Ollama, we use the ollama library directly
        
    def _prepare_messages(self, messages: list) -> list:
        """Prepare messages for the LLM, ensuring proper format."""
        # Ensure each message has required fields
        prepared = []
        for msg in messages:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                prepared.append(msg)
            else:
                # Assume it's user content if not properly formatted
                prepared.append({"role": "user", "content": str(msg)})
        return prepared
    
    def chat_complete(self, messages: list, model: Optional[str] = None) -> str:
        """Get a chat completion from the configured backend."""
        model_name = model or self.config.default_model
        prepared_messages = self._prepare_messages(messages)
        
        if self.config.backend == "ollama":
            try:
                response = ollama.chat(
                    model=model_name,
                    messages=prepared_messages,
                    options={
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens
                    }
                )
                return response['message']['content']
            except Exception as e:
                raise RuntimeError(f"Error with Ollama: {str(e)}")
                
        elif self.config.backend == "lmstudio":
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=prepared_messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                return response.choices[0].message.content
            except Exception as e:
                raise RuntimeError(f"Error with LM Studio: {str(e)}")
        else:
            raise ValueError(f"Unsupported backend: {self.config.backend}")
    
    def stream_chat(self, messages: list, model: Optional[str] = None) -> Generator[str, None, None]:
        """Stream chat completions from the configured backend."""
        model_name = model or self.config.default_model
        prepared_messages = self._prepare_messages(messages)
        
        if self.config.backend == "ollama":
            try:
                stream = ollama.chat(
                    model=model_name,
                    messages=prepared_messages,
                    options={
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens
                    },
                    stream=True
                )
                for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        yield chunk['message']['content']
            except Exception as e:
                raise RuntimeError(f"Error streaming with Ollama: {str(e)}")
                
        elif self.config.backend == "lmstudio":
            try:
                stream = self.client.chat.completions.create(
                    model=model_name,
                    messages=prepared_messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            except Exception as e:
                raise RuntimeError(f"Error streaming with LM Studio: {str(e)}")
        else:
            raise ValueError(f"Unsupported backend: {self.config.backend}")
    
    def list_models(self) -> list:
        """List available models from the configured backend."""
        if self.config.backend == "ollama":
            try:
                response = ollama.list()
                return [model['name'] for model in response['models']]
            except Exception as e:
                raise RuntimeError(f"Error listing Ollama models: {str(e)}")
                
        elif self.config.backend == "lmstudio":
            try:
                # Try to get models from the /models endpoint (OpenAI-compatible)
                response = requests.get(f"{self.config.lmstudio_base_url}/models", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return [model.get('id', model.get('name', 'unknown')) for model in data.get('data', [])]
                else:
                    # If /models endpoint doesn't exist, return default
                    return [self.config.default_model]
            except requests.exceptions.RequestException:
                # If request fails, return default model
                return [self.config.default_model]
            except Exception as e:
                raise RuntimeError(f"Error listing LM Studio models: {str(e)}")
        else:
            raise ValueError(f"Unsupported backend: {self.config.backend}")
    
    def test_connection(self) -> bool:
        """Test connection to the configured backend."""
        try:
            if self.config.backend == "ollama":
                # Test if ollama is running by listing models
                ollama.list()
                return True
            elif self.config.backend == "lmstudio":
                # Test connection to LM Studio API
                response = requests.get(f"{self.config.lmstudio_base_url}/models", timeout=5)
                return response.status_code == 200
            else:
                return False
        except:
            return False