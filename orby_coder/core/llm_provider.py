"""Core LLM integration for Orby Coder."""
import requests
import json
from typing import Generator, Dict, Any, Optional
from pathlib import Path
import ollama
from openai import OpenAI
from orby_coder.config.config_manager import ModelConfig
from orby_coder.utils.advanced import WebSearcher, TerminalExecutor

class LocalLLMProvider:
    """Handles communication with local LLM backends."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = None
        self.web_searcher = WebSearcher()
        self.terminal_executor = TerminalExecutor()
        
        if config.backend == "lmstudio":
            # LM Studio uses OpenAI-compatible API
            self.client = OpenAI(base_url=config.lmstudio_base_url, api_key="dummy")
        # For Ollama, we use the ollama library directly
    
    def _prepare_messages(self, messages: list, context: Optional[Dict] = None) -> list:
        """Prepare messages for the LLM, ensuring proper format and adding context if needed."""
        # Add context to messages if provided
        prepared = []
        for msg in messages:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                prepared.append(msg)
            else:
                # Assume it's user content if not properly formatted
                prepared.append({"role": "user", "content": str(msg)})
        
        # If we have context, add it to the conversation
        if context:
            # Add context to the beginning of the conversation
            context_msg = f"Additional context:\n{json.dumps(context, indent=2)}"
            prepared.insert(1, {"role": "user", "content": context_msg})
        
        return prepared
    
    def _enhanced_process(self, user_prompt: str) -> tuple:
        """Process user prompt for special commands and context."""
        # Check if user wants to execute a command or search
        context = {}
        
        # Check for terminal command indicators
        if any(cmd in user_prompt.lower() for cmd in ['execute:', 'run:', 'terminal:', 'command:']):
            # Extract command from prompt
            parts = user_prompt.split(':', 1)
            if len(parts) > 1:
                command = parts[1].strip()
                if self.config.enable_terminal_execution and TerminalExecutor.safe_command(command):
                    exec_result = TerminalExecutor.execute_command(command)
                    context['terminal_output'] = exec_result
        
        # Check for web search indicators
        if any(search_term in user_prompt.lower() for search_term in ['search:', 'find:', 'lookup:', 'google:', 'web:']):
            if self.config.enable_online_search:
                # Extract search query from prompt
                search_query = user_prompt
                for term in ['search:', 'find:', 'lookup:', 'google:', 'web:']:
                    if term in user_prompt.lower():
                        search_query = user_prompt.lower().split(term, 1)[1].strip()
                        break
                search_results = self.web_searcher.search(search_query)
                context['web_search_results'] = search_results
        
        return context
    
    def chat_complete(self, messages: list, model: Optional[str] = None, enable_context: bool = True) -> str:
        """Get a chat completion from the configured backend with enhanced features."""
        model_name = model or self.config.default_model
        
        # Process first message for special commands if it's a user message
        context = {}
        if enable_context and messages and messages[0].get('role') == 'user':
            context = self._enhanced_process(messages[0].get('content', ''))
        
        prepared_messages = self._prepare_messages(messages, context)
        
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
                error_msg = str(e)
                if "not found" in error_msg.lower():
                    raise RuntimeError(f"Model '{model_name}' not found. Please pull the model first with: ollama pull {model_name}")
                else:
                    raise RuntimeError(f"Error with Ollama: {error_msg}")
                
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
    
    def stream_chat(self, messages: list, model: Optional[str] = None, enable_context: bool = True) -> Generator[str, None, None]:
        """Stream chat completions from the configured backend with enhanced features."""
        model_name = model or self.config.default_model
        
        # Process first message for special commands if it's a user message
        context = {}
        if enable_context and messages and messages[0].get('role') == 'user':
            context = self._enhanced_process(messages[0].get('content', ''))
        
        prepared_messages = self._prepare_messages(messages, context)
        
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
                error_msg = str(e)
                if "not found" in error_msg.lower():
                    raise RuntimeError(f"Model '{model_name}' not found. Please pull the model first with: ollama pull {model_name}")
                else:
                    raise RuntimeError(f"Error streaming with Ollama: {error_msg}")
                
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
                # Handle different response formats
                if 'models' in response:
                    models = response['models']
                    # Extract model names, handling different key structures
                    model_names = []
                    for model in models:
                        if isinstance(model, dict):
                            # Try different possible keys for model name
                            name = model.get('name') or model.get('model') or model.get('id')
                            if name:
                                model_names.append(name)
                        else:
                            # If model is a string
                            model_names.append(str(model))
                    return model_names if model_names else [self.config.default_model]
                else:
                    # Fallback to default model if response format is unexpected
                    return [self.config.default_model]
            except Exception as e:
                # Return default model if listing fails
                print(f"Warning: Could not list Ollama models: {str(e)}")
                return [self.config.default_model]
                
        elif self.config.backend == "lmstudio":
            try:
                # Try to get models from the /models endpoint (OpenAI-compatible)
                response = requests.get(f"{self.config.lmstudio_base_url}/models", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Handle different response formats
                    if 'data' in data:
                        models_data = data['data']
                    elif 'models' in data:
                        models_data = data['models']
                    else:
                        models_data = []
                    
                    model_names = []
                    for model in models_data:
                        if isinstance(model, dict):
                            # Try different possible keys for model name
                            name = model.get('id') or model.get('name') or model.get('model')
                            if name:
                                model_names.append(name)
                        else:
                            # If model is a string
                            model_names.append(str(model))
                    
                    return model_names if model_names else [self.config.default_model]
                else:
                    # If /models endpoint doesn't exist, return default
                    return [self.config.default_model]
            except requests.exceptions.RequestException:
                # If request fails, return default model
                return [self.config.default_model]
            except Exception as e:
                # Return default model if listing fails
                print(f"Warning: Could not list LM Studio models: {str(e)}")
                return [self.config.default_model]
        else:
            # Return default model for unsupported backends
            return [self.config.default_model]
    
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