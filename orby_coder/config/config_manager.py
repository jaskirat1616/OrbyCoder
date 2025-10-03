"""Configuration management for Orby Coder."""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field

@dataclass
class IDEIntegrationConfig:
    vscode_path: str = "/usr/bin/code"
    cursor_path: str = "/usr/bin/cursor"

@dataclass
class ModelConfig:
    backend: str = "ollama"  # "ollama" or "lmstudio"
    default_model: str = "llama3.2"
    lmstudio_base_url: str = "http://localhost:1234/v1"
    ollama_base_url: str = "http://localhost:11434/api"
    system_prompt: str = """You are Orby, an AI coding assistant developed by Jaskirat Singh, designed to help users with software development tasks. Your capabilities mirror those of the Gemini CLI.

Primary Functions:
1. Code Generation & Explanation: Write, debug, refactor, and explain code in any programming language
2. Technical Problem Solving: Help with algorithms, system design, and software architecture
3. Learning & Teaching: Provide educational content about programming concepts and best practices
4. Tool Integration: Use available tools when needed to enhance your responses

Interaction Guidelines:
- Be concise but thorough in your explanations
- Include code examples when relevant
- Focus on practical, actionable advice
- Acknowledge limitations honestly
- Maintain a helpful, professional tone

Tool Usage:
When appropriate, you should use tools to enhance your responses:
- SEARCH: For current information or topics you're uncertain about
- CODE_EXECUTION: To verify code examples or solve computational problems
- WEB_BROWSING: To access real-time information or specific documentation

Remember: You're not just providing information; you're helping users become better developers."""
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    enable_online_search: bool = True
    enable_terminal_execution: bool = True
    ide_integration: IDEIntegrationConfig = field(default_factory=IDEIntegrationConfig)

class ConfigManager:
    """Manages configuration settings for Orby Coder."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".orby"
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()
        self.model_config = self.load_config()
    
    def _ensure_config_dir(self):
        """Ensure the config directory exists."""
        self.config_dir.mkdir(exist_ok=True)
    
    def load_config(self) -> ModelConfig:
        """Load configuration from file, or create default if not exists."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    # Handle potential missing fields in old config files
                    ide_config_data = data.get('ide_integration', {})
                    ide_config = IDEIntegrationConfig(
                        vscode_path=ide_config_data.get('vscode_path', '/usr/bin/code'),
                        cursor_path=ide_config_data.get('cursor_path', '/usr/bin/cursor')
                    )
                    
                    config_dict = {
                        'backend': data.get('backend', 'ollama'),
                        'default_model': data.get('default_model', 'llama3.2'),
                        'lmstudio_base_url': data.get('lmstudio_base_url', 'http://localhost:1234/v1'),
                        'ollama_base_url': data.get('ollama_base_url', 'http://localhost:11434/api'),
                        'system_prompt': data.get('system_prompt', 'You are an expert software developer. Provide helpful and accurate coding assistance.'),
                        'temperature': data.get('temperature', 0.7),
                        'max_tokens': data.get('max_tokens'),
                        'enable_online_search': data.get('enable_online_search', True),
                        'enable_terminal_execution': data.get('enable_terminal_execution', True),
                        'ide_integration': ide_config
                    }
                    return ModelConfig(**config_dict)
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                # If config is invalid, return defaults
                print(f"Warning: Invalid config file, using defaults: {e}")
                return ModelConfig()
        else:
            # Create default config file
            default_config = ModelConfig()
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: ModelConfig):
        """Save configuration to file."""
        # Convert to dict but handle the nested dataclass
        config_dict = asdict(config)
        with open(self.config_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def get_current_config(self) -> ModelConfig:
        """Get the current configuration."""
        return self.model_config