"""UI command for Orby Coder using Textual."""
import typer
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, TextArea, Static, ListView, ListItem, Label
from textual import events
from rich.text import Text
import asyncio
from orby_coder.core.llm_provider import LocalLLMProvider
from orby_coder.config.config_manager import ConfigManager

console_app = typer.Typer()

class ChatHistoryList(ListView):
    """Display chat history."""
    def __init__(self):
        super().__init__()
        self.messages = []
    
    def add_message(self, role: str, content: str):
        """Add a message to the chat history."""
        message_text = f"[{role}]: {content[:50]}..." if len(content) > 50 else f"[{role}]: {content}"
        self.append(ListItem(Static(message_text)))
        self.messages.append((role, content))

class CodeView(ScrollableContainer):
    """Display code content."""
    def __init__(self):
        super().__init__()
        self.code_content = Static("")
        self.mount(self.code_content)
    
    def update_code(self, code: str):
        """Update the displayed code."""
        self.code_content.update(code)

class InputWidget(TextArea):
    """Input field for prompts."""
    pass

class StatusBar(Static):
    """Status bar showing active model and backend."""
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.update_status()
    
    def update_status(self):
        self.update(
            f"Active Model: {self.config.default_model} | Backend: {self.config.backend} | "
            f"Orby Coder v0.1.0"
        )

class OrbyTUI(App):
    """Main Textual application for Orby Coder."""
    
    CSS = """
    #chat-history-panel {
        width: 30%;
        height: 1fr;
        border: tall $primary;
        margin-right: 1;
    }
    
    #code-view-panel {
        width: 70%;
        height: 1fr;
        border: tall $secondary;
    }
    
    #input-container {
        height: 10;
        border: tall $accent;
        margin-top: 1;
    }
    
    .panel-title {
        text-style: bold;
        background: $primary 10%;
        padding: 0 1;
    }
    
    .status-bar {
        height: 1;
        dock: bottom;
        background: $surface;
        color: $text;
        content-align: left middle;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+d", "quit", "Quit"),
        ("t", "theme_toggle", "Toggle Dark/Light"),
        ("s", "switch_model", "Switch Model"),
    ]
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.llm = LocalLLMProvider(config)
        self.chat_history = ChatHistoryList()
        self.code_view = CodeView()
        self.input_widget = InputWidget(placeholder="Enter your prompt here, or 'help' for commands...")
        
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        
        with Horizontal():
            # Left panel: Chat history
            with Vertical(id="chat-history-panel"):
                yield Static("Chat History", classes="panel-title")
                yield self.chat_history
            
            # Right panel: Code/files view
            with Vertical(id="code-view-panel"):
                yield Static("Code View", classes="panel-title")
                yield self.code_view
        
        # Bottom input bar
        with Container(id="input-container"):
            yield self.input_widget
        
        # Status bar
        status_bar = Static()
        status_bar.add_class("status-bar")
        status_bar.update(
            f"Active Model: {self.config.default_model} | Backend: {self.config.backend} | "
            f"Orby Coder v0.1.0"
        )
        yield status_bar
    
    def on_mount(self) -> None:
        """Called when app starts."""
        # Focus the input widget
        self.input_widget.focus()
        
        # Add welcome message
        self.chat_history.add_message("System", "Welcome to Orby Coder! Type 'help' for available commands.")
    
    def on_text_area_submitted(self, message: TextArea.Submitted) -> None:
        """Handle text input submission."""
        if message.control == self.input_widget:
            prompt = message.control.text.strip()
            if not prompt:
                return
            
            # Check for special commands
            if prompt.lower() == 'help':
                help_text = (
                    "Commands:\n"
                    "- Type 'help' to see this message\n"
                    "- Type 'models' to list available models\n"
                    "- Type 'config' to see current config\n"
                    "- Type 'clear' to clear chat history\n"
                    "- Type 'quit' or 'exit' to quit\n"
                    "- Any other text is sent to the AI"
                )
                self.chat_history.add_message("System", help_text)
                self.input_widget.text = ""
                return
            elif prompt.lower() == 'models':
                try:
                    models = self.llm.list_models()
                    models_list = "\n".join([f"- {model}" for model in models])
                    self.chat_history.add_message("System", f"Available models:\n{models_list}")
                except Exception as e:
                    self.chat_history.add_message("System", f"Error listing models: {str(e)}")
                self.input_widget.text = ""
                return
            elif prompt.lower() == 'config':
                config_info = (
                    f"Backend: {self.config.backend}\n"
                    f"Default Model: {self.config.default_model}\n"
                    f"LM Studio URL: {self.config.lmstudio_base_url}\n"
                    f"System Prompt: {self.config.system_prompt[:50]}..."
                )
                self.chat_history.add_message("System", config_info)
                self.input_widget.text = ""
                return
            elif prompt.lower() in ['clear', 'cls']:
                self.chat_history.clear()
                self.chat_history.add_message("System", "Chat history cleared.")
                self.input_widget.text = ""
                return
            elif prompt.lower() in ['quit', 'exit']:
                self.exit()
                return
            
            # Add user message to history
            self.chat_history.add_message("You", prompt)
            
            # Process with AI
            messages = [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            try:
                # Get response from LLM
                response = self.llm.chat_complete(messages)
                
                # Add AI response to history
                self.chat_history.add_message("Orby", response)
                
                # If response contains code, display it in the code view
                if "```" in response:
                    # Simple extraction of first code block
                    parts = response.split("```")
                    if len(parts) > 1:
                        code_block = parts[1].split('\n', 1)[-1]  # Remove language specifier line
                        code_block = code_block.rsplit('\n', 1)[0]  # Remove closing ```
                        self.code_view.update_code(code_block)
                
            except Exception as e:
                self.chat_history.add_message("System", f"Error: {str(e)}")
            
            # Clear input
            self.input_widget.text = ""
            self.input_widget.focus()
    
    def action_theme_toggle(self) -> None:
        """Toggle between dark and light mode."""
        self.dark = not self.dark
    
    def action_switch_model(self) -> None:
        """Switch to a different model."""
        # This would open a model selection dialog in a full implementation
        self.chat_history.add_message("System", "Model switching functionality would open here.")

def ui_command(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use for inference")
):
    """Launch the Textual-based interactive UI."""
    config_manager = ConfigManager()
    config = config_manager.get_current_config()
    
    if model:
        config.default_model = model
    
    app = OrbyTUI(config)
    app.run()