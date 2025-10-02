# Orby Coder

Orby Coder is an open-source AI CLI tool designed for coding and development. It provides local-first AI assistance through Ollama or LM Studio, offering features like chat, code generation, file execution, and an interactive TUI.

## 🚀 Features

- **Local AI Models**: Use Ollama or LM Studio for privacy-focused AI assistance
- **Interactive Chat**: Engage in conversations with AI about code
- **Code Generation**: Generate, modify, and explain code snippets
- **File Execution**: Run and analyze code files with AI-powered explanations
- **Interactive TUI**: Rich terminal user interface powered by Textual
- **Configurable**: Easy configuration for different backends and models

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Ollama or LM Studio (for local AI models)

### Install Orby Coder

```bash
pip install orby-coder
```

## 💻 How to Run

### Interactive UI (Recommended)
```bash
orby ui
```
This launches the Gemini CLI-like interface with chat panel and code viewer.

### Other Commands
```bash
# Interactive chat mode
orby chat

# Single prompt chat
orby chat "Explain how this function works" --file my_function.py

# Code generation
orby code "Create a Python class for a binary tree"

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

## ⚙️ Configuration

Orby Coder uses a configuration file at `~/.orby/config.json`. The default configuration is:

```json
{
  "backend": "ollama",
  "default_model": "llama3.2",
  "lmstudio_base_url": "http://localhost:1234/v1",
  "ollama_base_url": "http://localhost:1234/api",
  "system_prompt": "You are an expert software developer. Provide helpful and accurate coding assistance."
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