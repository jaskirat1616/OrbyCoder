"""Core LLM integration for Orby Coder - Gemini CLI style tool usage."""
import requests
import json
from typing import Generator, Dict, Any, Optional, List
from pathlib import Path
import ollama
from openai import OpenAI
from orby_coder.config.config_manager import ModelConfig
from orby_coder.core.tools import ShellTool, WebSearchTool, ReadFileTool
from datetime import datetime
import subprocess
import os
import platform
from orby_coder.utils.advanced import WebSearcher, TerminalExecutor, ToolManager

class LocalLLMProvider:
    """Handles communication with local LLM backends."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = None
        
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
    
    def _enhanced_process(self, user_prompt: str) -> dict:
        """Process user prompt for special commands and context - Gemini CLI style tool usage."""
        context = {}
        
        # Use new tools implementation for enhanced tool processing
        user_prompt_lower = user_prompt.lower()
        
        # Terminal execution tool - Gemini CLI style detection
        if self.config.enable_terminal_execution:
            terminal_triggers = [
                'execute:', 'run:', 'terminal:', 'command:', 
                'can you run', 'please run', 'try running',
                'run this command', 'execute this', 'terminal command'
            ]
            
            if any(trigger in user_prompt_lower for trigger in terminal_triggers):
                # Extract command using regex-like approach
                command_indicators = ['execute:', 'run:', 'terminal:', 'command:']
                for indicator in command_indicators:
                    if indicator in user_prompt_lower:
                        command = user_prompt.split(indicator, 1)[1].strip()
                        if command:
                            # Use ShellTool to execute command
                            shell_tool = ShellTool()
                            validation_result = shell_tool.validate_params({"command": command})
                            if not validation_result:  # No validation error
                                # Check if confirmation is needed
                                confirmation_needed = shell_tool.should_confirm_execute({"command": command})
                                if confirmation_needed:
                                    # In a real implementation, this would prompt user
                                    # For now, we'll proceed with execution
                                    pass
                                
                                # Execute the tool
                                result = shell_tool.execute({"command": command})
                                context['terminal_execution'] = result
                        break
        
        # Web search tool - Gemini CLI style detection
        if self.config.enable_online_search:
            search_triggers = [
                'search:', 'find:', 'lookup:', 'google:', 'web:',
                'can you search', 'please search', 'look up',
                'what is', 'who is', 'when was', 'how does', 'why is',
                'current status', 'latest news', 'recent updates'
            ]
            
            if any(trigger in user_prompt_lower for trigger in search_triggers):
                # Extract search query
                search_indicators = ['search:', 'find:', 'lookup:', 'google:', 'web:']
                search_query = user_prompt
                
                for indicator in search_indicators:
                    if indicator in user_prompt_lower:
                        search_query = user_prompt.split(indicator, 1)[1].strip()
                        break
                
                # If no explicit indicator, use the whole query for general search terms
                if search_query == user_prompt:
                    # Check for general knowledge questions
                    question_indicators = [
                        'what is', 'who is', 'when was', 'how does', 'why is',
                        'current', 'latest', 'recent', 'news', 'status'
                    ]
                    for q_indicator in question_indicators:
                        if q_indicator in user_prompt_lower:
                            search_query = user_prompt
                            break
                
                if search_query:
                    # Use WebSearchTool to perform search
                    web_search_tool = WebSearchTool()
                    result = web_search_tool.execute({"query": search_query})
                    context['web_search'] = result
        
        # File system tool - check if user is asking about specific files
        file_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.go', '.rs', '.swift']
        file_triggers = ['file:', 'read file', 'open file', 'contents of', 'show me the file']
        
        if (any(ext in user_prompt_lower for ext in file_extensions) or 
            any(trigger in user_prompt_lower for trigger in file_triggers)):
            # This would be implemented for file reading capabilities using ReadFileTool
            pass
        
        return context
    
    def chat_complete(self, messages: list, model: Optional[str] = None, enable_context: bool = True) -> str:
        """Get a chat completion from the configured backend with enhanced features."""
        model_name = model or self.config.default_model
        
        # Process first message for special commands if it's a user message
        context = {}
        if enable_context and messages and messages[0].get('role') == 'user':
            context = self._enhanced_process(messages[0].get('content', ''))
        
        # Enhance messages with tool usage context if needed
        prepared_messages = self._prepare_messages(messages, context)
        
        # Add tool usage instructions to system prompt for better tool utilization
        if context:
            tool_instructions = (
                "\n\n[TOOL USAGE INSTRUCTIONS]\n"
                "You have access to the following tools that can be used when appropriate:\n"
            )
            
            if 'terminal_execution' in context:
                tool_instructions += (
                    "TERMINAL EXECUTION: You can execute commands to verify code, run tests, or gather system information.\n"
                    "Usage: Prefix your response with TERMINAL: followed by the command to execute.\n"
                )
            
            if 'web_search' in context:
                tool_instructions += (
                    "WEB SEARCH: You can search the web for current information or topics you're uncertain about.\n"
                    "Usage: Prefix your response with SEARCH: followed by your search query.\n"
                )
            
            # Add tool instructions to the last system message or create one
            system_message_found = False
            for i, msg in enumerate(prepared_messages):
                if msg.get('role') == 'system':
                    if isinstance(msg.get('content'), str):
                        prepared_messages[i]['content'] += tool_instructions
                    system_message_found = True
                    break
            
            # If no system message found, add one at the beginning
            if not system_message_found:
                prepared_messages.insert(0, {"role": "system", "content": self.config.system_prompt + tool_instructions})
        
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
        
        # Enhance messages with tool usage context if needed
        prepared_messages = self._prepare_messages(messages, context)
        
        # Add tool usage instructions to system prompt for better tool utilization
        if context:
            tool_instructions = (
                "\n\n[TOOL USAGE INSTRUCTIONS]\n"
                "You have access to the following tools that can be used when appropriate:\n"
            )
            
            if 'terminal_execution' in context:
                tool_instructions += (
                    "TERMINAL EXECUTION: You can execute commands to verify code, run tests, or gather system information.\n"
                    "Usage: Prefix your response with TERMINAL: followed by the command to execute.\n"
                )
            
            if 'web_search' in context:
                tool_instructions += (
                    "WEB SEARCH: You can search the web for current information or topics you're uncertain about.\n"
                    "Usage: Prefix your response with SEARCH: followed by your search query.\n"
                )
            
            # Add tool instructions to the last system message or create one
            system_message_found = False
            for i, msg in enumerate(prepared_messages):
                if msg.get('role') == 'system':
                    if isinstance(msg.get('content'), str):
                        prepared_messages[i]['content'] += tool_instructions
                    system_message_found = True
                    break
            
            # If no system message found, add one at the beginning
            if not system_message_found:
                prepared_messages.insert(0, {"role": "system", "content": self.config.system_prompt + tool_instructions})
        
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