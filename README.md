# Orby Coder

Orby Coder is an open-source AI CLI tool designed for coding and development. It provides local-first AI assistance through Ollama or LM Studio, with IDE integration, file editing, terminal execution, and online search capabilities. The interface matches Gemini CLI design using Textual widgets.

## 🚀 Features

- **Local AI Models**: Use Ollama or LM Studio for privacy-focused AI assistance
- **Interactive Chat**: Engage in conversations with AI about code
- **Code Generation**: Generate, modify, and explain code snippets
- **File Editing**: Direct file modification with AI assistance
- **Terminal Execution**: Execute commands with user permissions
- **Online Search**: Search the web when needed for context
- **IDE Integration**: Connect with VSCode, Cursor and other editors
- **Interactive TUI**: Rich Gemini CLI-like terminal UI powered by Textual
- **Configurable**: Easy configuration for different backends and models

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Ollama or LM Studio (for local AI models)

### Install Orby Coder

```bash
pip install orby-coder
```

Or install from source:

```bash
git clone https://github.com/jaskirat1616/OrbyCoder.git
cd OrbyCoder
pip install -e .
```

## 💻 How to Run

### Interactive UI (Gemini CLI-like)
```bash
orby ui
```
This launches the Gemini CLI-like interface with chat panel, code viewer, and advanced features.

### Other Commands
```bash
# Interactive chat mode
orby chat

# Single prompt chat
orby chat "Explain how this function works" --file my_function.py

# Code generation and editing
orby code "Fix the bug in this function" --file buggy_code.py

# Run a file with AI analysis
orby run script.py --explain

# Get help
orby --help
orby chat --help
```

### Interactive UI Features

The UI features a Gemini CLI-like interface:
- Left panel: Chat history with message bubbles
- Right panel: Code viewer (toggles when code is detected)
- Bottom: Input field with "Message Orby..." placeholder
- Top: Header with app name and clock
- Bottom: Status bar showing active model
- Animated "typing" indicator when AI is responding

### Interactive Chat Commands

In the interactive chat mode, you can use these special commands:
- `help` - Show help message
- `models` - List available models
- `model <name>` - Change current model
- `config` - Show current configuration
- `temperature <value>` - Set temperature (0.0-1.0)
- `clear` - Clear screen
- `execute: command` - Execute terminal command
- `search: query` - Search the web
- `exit/quit/q` - Exit the application
- IDE integration controls
- Online search integration

## ⚙️ Configuration

Orby Coder uses a configuration file at `~/.orby/config.json`. The default configuration is:

```json
{
  "backend": "ollama",
  "default_model": "llama3.2",
  "lmstudio_base_url": "http://localhost:1234/v1",
  "ollama_base_url": "http://localhost:11434/api",
  "system_prompt": "You are an expert software developer. Provide helpful and accurate coding assistance.",
  "enable_online_search": true,
  "enable_terminal_execution": true,
  "ide_integration": {
    "vscode_path": "/usr/bin/code",
    "cursor_path": "/usr/bin/cursor"
  }
}
```

You can modify this file to change your default settings. Orby Coder will create this file automatically on first run.

## 🤖 Supported Backends

### Ollama
1. Install [Ollama](https://ollama.com/)
2. Pull a model: `ollama pull llama3.2`
3. Run: `ollama serve` (in a separate terminal)

### LM Studio
1. Install [LM Studio](https://lmstudio.ai/)
2. Load a model and start the local server on port 1234
3. Orby Coder will automatically connect to `http://localhost:1234/v1`

## 📚 Commands

| Command | Description |
|--------|-------------|
| `orby chat [PROMPT]` | Chat with the AI assistant |
| `orby code PROMPT` | Generate or modify code |
| `orby run FILE` | Execute a file with optional explanation |
| `orby ui` | Launch the interactive TUI |
| `orby --help` | Show help information |

## 🖥️ Advanced Features

### File Editing
- Direct file modification with AI suggestions
- Context-aware code completion
- Intelligent refactoring support

### Terminal Execution
- Execute shell commands with user permissions
- Safe command validation
- Output analysis with AI

### Online Search
- Web search integration for knowledge
- Context-aware search queries
- Result summarization by AI

### IDE Integration
- VSCode integration
- Cursor editor support
- File opening and editing

## 🔧 Development

To contribute to Orby Coder:

```bash
# Clone the repository
git clone https://github.com/jaskirat1616/OrbyCoder.git
cd OrbyCoder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install -e ".[dev]"
```

## 📄 License

Apache 2.0 License - Copyright 2025 Orby Project Contributors

See the [LICENSE](LICENSE) file for more details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for more details.

## 🐛 Issues

If you encounter any issues, please file them in the [GitHub Issues](https://github.com/jaskirat1616/OrbyCoder/issues) section.