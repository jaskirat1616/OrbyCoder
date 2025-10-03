"""UI command for Orby Coder using Textual."""
import typer
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, TextArea, Static, ListView, ListItem, Label, LoadingIndicator
from textual import events
from rich.text import Text
from rich.markdown import Markdown
import asyncio
from orby_coder.core.llm_provider import LocalLLMProvider
from orby_coder.config.config_manager import ConfigManager
from textual.reactive import reactive
from textual.widgets import RichLog
from textual.binding import Binding
from textual.widgets._markdown import Markdown as MarkdownWidget
from orby_coder.utils.advanced import TerminalExecutor, WebSearcher, IDEIntegration

console_app = typer.Typer()

class ThinkingAnimation(Static):
    """A widget for showing a thinking animation."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dots = 0
        self.update(f"[italic blue]●●●[/italic blue]")
        
    def on_mount(self) -> None:
        self.set_interval(0.5, self._update_dots)
        
    def _update_dots(self) -> None:
        self.dots = (self.dots + 1) % 4
        dots_str = "●" * (self.dots + 1) + "○" * (3 - self.dots)
        self.update(f"[italic blue]{dots_str}[/italic blue]")

class MessageContainer(Vertical):
    """Container for a single message with role and content."""
    
    def __init__(self, role: str, content: str):
        super().__init__()
        self.role = role
        self.content = content
        
    def compose(self) -> ComposeResult:
        # Use markdown for content to support rich formatting
        markdown_content = MarkdownWidget(self.content)
        
        if self.role == "You":
            # User message styling
            with Horizontal(classes="message-container user-message"):
                yield Static("👤 You", classes="message-role user-role")
                yield Container(markdown_content, classes="message-content user-content")
        else:
            # Assistant message styling
            with Horizontal(classes="message-container assistant-message"):
                yield Static("🤖 Orby", classes="message-role assistant-role")
                yield Container(markdown_content, classes="message-content assistant-content")

class ChatHistoryContainer(ScrollableContainer):
    """Display chat history with proper message formatting."""
    
    def __init__(self):
        super().__init__()
        self.messages = []
        self._messages_to_add = []  # Store messages until mounted
        self.border_title = "Chat"
    
    def compose(self) -> ComposeResult:
        """Compose the widget."""
        # Add any pre-mounted messages
        for role, content in self._messages_to_add:
            yield MessageContainer(role, content)
            self.messages.append((role, content))
        self._messages_to_add.clear()
    
    def add_message(self, role: str, content: str):
        """Add a message to the chat history."""
        if self.is_mounted:
            message_container = MessageContainer(role, content)
            self.mount(message_container)
            self.scroll_end(animate=False, speed=50)
            self.messages.append((role, content))
        else:
            # Store for when widget is mounted
            self._messages_to_add.append((role, content))
    
    def clear_messages(self):
        """Clear all messages from the chat history."""
        for child in self.children:
            child.remove()
        self.messages.clear()
        self._messages_to_add.clear()

class CodeView(ScrollableContainer):
    """Display code content."""
    
    def __init__(self):
        super().__init__()
        self.border_title = "Code View"
        self.code_content = Static("", classes="code-display")
    
    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield self.code_content
    
    def update_code(self, code: str):
        """Update the displayed code."""
        self.code_content.update(code)

class InputWidget(TextArea):
    """Input field for prompts."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_line_numbers = False
        self.max_content_width = 80
        self.language = "text"

class StatusBar(Static):
    """Status bar showing active model and backend."""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.update_status()
    
    def update_status(self):
        self.update(
            f" Orby Coder | Model: {self.config.default_model} | Backend: {self.config.backend} | Online: {'ON' if self.config.enable_online_search else 'OFF'} | Terminal: {'ON' if self.config.enable_terminal_execution else 'OFF'} "
        )

class OrbyTUI(App):
    """Main Textual application for Orby Coder - closely matching Gemini CLI UI."""
    
    CSS = """
    Screen {
        background: #1e1e1e;  /* Dark background like Gemini */
        color: #e0e0e0;       /* Light text */
        layers: base floating;
    }

    Header {
        background: #333333;  /* Darker header */
        color: #ffffff;
        height: 1;
        text-style: bold;
    }
    
    #main-container {
        layout: vertical;
        height: 1fr;
    }
    
    #chat-container {
        layout: horizontal;
        height: 1fr;
        border: none;
    }
    
    #chat-history-panel {
        width: 1fr;
        height: 1fr;
        min-width: 50;
        border: none;
        background: #2d2d2d;  /* Slightly lighter than background */
    }
    
    #code-view-panel {
        width: 40;
        height: 1fr;
        border-left: solid #444444;
        display: block;
        background: #252526;   /* Code panel background */
    }
    
    #input-container {
        height: 8;             /* Smaller input area like Gemini */
        border-top: solid #444444;
        padding: 1 1 0 1;
        background: #3c3c3c;  /* Input area background */
    }
    
    #status-bar {
        height: 1;
        dock: bottom;
        background: #333333;
        color: #cccccc;
        content-align: left middle;
        border-top: solid #444444;
        text-opacity: 90%;
        font-size: small;
    }
    
    .message-container {
        padding: 1 2;          /* More padding like Gemini */
        width: 1fr;
        border-bottom: solid #3a3a3a 1;  /* Subtle separators */
    }
    
    .user-message {
        background: #2d2d2d;
    }
    
    .assistant-message {
        background: #252526;
    }
    
    .message-role {
        width: 12;             /* Narrower role column */
        text-style: bold;
        text-opacity: 85%;
        padding-right: 1;
    }
    
    .user-role {
        color: #4ec9b0;        /* Teal color for user */
    }
    
    .assistant-role {
        color: #569cd6;        /* Blue color for assistant like Gemini */
    }
    
    .message-content {
        width: 1fr;
        padding-left: 1;
        color: #d4d4d4;        /* Light text */
    }
    
    .user-content {
        color: #d4d4d4;
    }
    
    .assistant-content {
        color: #d4d4d4;
    }
    
    .code-display {
        background: #1e1e1e;   /* Dark code background */
        padding: 1;
        height: 1fr;
        border: solid #3c3c3c 1;
    }
    
    .thinking-container {
        height: 3;
        content-align: center middle;
        padding: 1;
        background: #252526;
    }
    
    #thinking-indicator {
        text-opacity: 70%;
        color: #569cd6;        /* Blue color for thinking indicator */
    }
    
    TextArea {
        border: none;
        background: #3c3c3c;
        color: #ffffff;
        height: 1fr;
        min-height: 5;
        padding: 1;
    }
    
    .markdown {
        text-opacity: 100%;
    }
    
    /* Gemini-like styling for code blocks */
    .code-block {
        background: #1e1e1e;
        border: solid #3c3c3c 1;
        padding: 1;
    }
    
    /* Scrollbar styling */
    .-scrollbar {
        background: #3c3c3c;
    }
    
    .-scrollbar-thumb {
        background: #555555;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+d", "quit", "Quit", show=False),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("f5", "regenerate_response", "Regenerate", show=True),
        Binding("ctrl+r", "regenerate_response", "Regenerate", show=False),
        Binding("ctrl+e", "toggle_code_view", "Toggle Code", show=True),
        Binding("ctrl+t", "terminal_panel", "Terminal", show=True),
        Binding("ctrl+s", "search_panel", "Search", show=True),
    ]
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.llm = LocalLLMProvider(config)
        self.ide_integration = IDEIntegration(config)
        self.chat_history = ChatHistoryContainer()
        self.code_view = CodeView()
        self.input_widget = InputWidget(placeholder="Message Orby...")
        self.thinking_indicator = ThinkingAnimation(id="thinking-indicator")
        self.thinking_container = Horizontal(classes="thinking-container", id="thinking-container")
        self.thinking_container.visible = False
        self.input_history = []
        self.history_index = -1
        self.current_response = ""
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(name="Orby", show_clock=True)
        
        with Vertical(id="main-container"):
            with Horizontal(id="chat-container"):
                # Left panel: Chat history
                with Vertical(id="chat-history-panel"):
                    yield self.chat_history
                    yield self.thinking_container  # Add container to the layout
                
                # Right panel: Code/files view (hidden by default)
                with Vertical(id="code-view-panel", classes="code-panel"):
                    yield self.code_view
                    self.code_view.display = False  # Hidden by default
        
        # Bottom input bar
        with Container(id="input-container"):
            yield self.input_widget
        
        # Status bar with Gemini-like styling
        yield Static(
            f" Model: {self.config.default_model} | Backend: {self.config.backend} | Search: {'ON' if self.config.enable_online_search else 'OFF'} | Terminal: {'ON' if self.config.enable_terminal_execution else 'OFF'} ",
            id="status-bar"
        )
    
    def on_mount(self) -> None:
        """Called when app starts - add children after mounting."""
        # Add the thinking indicator to its container after both are mounted
        self.thinking_container.mount(self.thinking_indicator)
        
        # Focus the input widget
        self.input_widget.focus()
        
        # Add welcome message similar to Gemini CLI
        welcome_msg = (
            "👋 Hello! I'm Orby, your AI coding assistant powered by Google DeepMind technology.\n\n"
            "**What I can help you with:**\n"
            "• 🧑‍💻 Explaining code and concepts\n"
            "• 🛠️ Generating and debugging code\n"
            "• 📚 Teaching programming fundamentals\n"
            "• 🔍 Researching technical topics\n"
            "• 🧪 Executing and testing code snippets\n\n"
            "**Getting Started:**\n"
            "Just type your coding question or task, and I'll assist you.\n"
            "Type `help` for a list of special commands.\n\n"
            "**Connected Tools:**\n"
            "• 🔗 Web Search (enabled)\n"
            "• 💻 Terminal Execution (enabled)\n"
            "• 📂 IDE Integration (VSCode, Cursor)\n\n"
            "*Powered by local AI models for privacy-focused assistance.*"
        )
        self.chat_history.add_message("Orby", welcome_msg)

    def on_text_area_submitted(self, message) -> None:
        """Handle text input submission."""
        if message.control == self.input_widget:
            prompt = message.control.text.strip()
            if not prompt:
                return
            
            # Add to input history
            if prompt not in self.input_history:
                self.input_history.append(prompt)
            self.history_index = -1  # Reset history index after new input
            
            # Check for special commands
            if prompt.lower() == 'help':
                help_text = (
                    "**Available Commands:**\n\n"
                    "- `help` - Show this help message\n"
                    "- `models` - List available models\n"
                    "- `config` - Show current configuration\n"
                    "- `system` - Show system information\n"
                    "- `clear` - Clear chat history\n"
                    "- `quit` or `exit` - Exit the application\n"
                    "- `temperature <value>` - Set temperature (0.0-1.0)\n\n"
                    "**Advanced Usage:**\n"
                    f"- `execute: command` - Execute terminal command (enabled: {self.config.enable_terminal_execution})\n"
                    f"- `search: query` - Web search (enabled: {self.config.enable_online_search})\n\n"
                    "**General Usage:**\n"
                    "Ask about code, request implementations, or explain concepts."
                )
                self.chat_history.add_message("Orby", help_text)
                self.input_widget.text = ""
                return
            elif prompt.lower() == 'models':
                try:
                    models = self.llm.list_models()
                    models_list = "\n".join([f"- {model}" for model in models])
                    self.chat_history.add_message("Orby", f"**Available models:**\n{models_list}")
                except Exception as e:
                    self.chat_history.add_message("Orby", f"**Error listing models:** {str(e)}")
                self.input_widget.text = ""
                return
            elif prompt.lower() == 'config':
                config_info = (
                    f"**Configuration:**\n"
                    f"- Backend: {self.config.backend}\n"
                    f"- Default Model: {self.config.default_model}\n"
                    f"- LM Studio URL: {self.config.lmstudio_base_url}\n"
                    f"- Ollama URL: {self.config.ollama_base_url}\n"
                    f"- Temperature: {self.config.temperature}\n"
                    f"- Online Search: {self.config.enable_online_search}\n"
                    f"- Terminal Execution: {self.config.enable_terminal_execution}\n"
                    f"- VSCode Path: {self.config.ide_integration.vscode_path}\n"
                    f"- Cursor Path: {self.config.ide_integration.cursor_path}"
                )
                self.chat_history.add_message("Orby", config_info)
                self.input_widget.text = ""
                return
            elif prompt.lower() == 'system':
                import psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                sys_info = (
                    f"**System Information:**\n"
                    f"- CPU Usage: {cpu_percent}%\n"
                    f"- Memory: {memory.percent}% used ({memory.available // (1024**3)}GB free)\n"
                    f"- Disk: {psutil.disk_usage('/').percent:.1f}% used"
                )
                self.chat_history.add_message("Orby", sys_info)
                self.input_widget.text = ""
                return
            elif prompt.lower() in ['clear', 'cls']:
                # Clear the chat history
                for child in self.chat_history.children:
                    if child != self.thinking_container:
                        child.remove()
                self.chat_history.messages.clear()
                self.chat_history.add_message("Orby", "Chat history cleared. How can I help you?")
                self.input_widget.text = ""
                return
            elif prompt.lower() in ['quit', 'exit', 'q']:
                self.exit()
                return
            elif prompt.lower().startswith('temperature '):
                try:
                    temp_str = prompt.lower().split(' ', 1)[1]
                    temp_value = float(temp_str)
                    if 0.0 <= temp_value <= 1.0:
                        self.config.temperature = temp_value
                        # Update the config manager as well
                        config_manager = ConfigManager()
                        updated_config = config_manager.get_current_config()
                        updated_config.temperature = temp_value
                        config_manager.save_config(updated_config)
                        
                        self.chat_history.add_message("Orby", f"**Temperature set to:** {temp_value}")
                    else:
                        self.chat_history.add_message("Orby", "**Temperature must be between 0.0 and 1.0**")
                except (ValueError, IndexError):
                    self.chat_history.add_message("Orby", "**Invalid temperature command. Use: `temperature <value>`**")
                self.input_widget.text = ""
                return
            
            # Check for special execution commands
            prompt_lower = prompt.lower()
            if prompt_lower.startswith('execute:') or prompt_lower.startswith('run:'):
                if self.config.enable_terminal_execution:
                    command = prompt[8:].strip()  # Remove 'execute:' or 'run:'
                    if TerminalExecutor.safe_command(command):
                        self.chat_history.add_message("You", f"**EXECUTING:** {command}")
                        result = TerminalExecutor.execute_command(command)
                        if result['success']:
                            response = f"**Command succeeded:**\n```\n{result['stdout']}\n```"
                            if result['stderr']:
                                response += f"\n**Errors:**\n```\n{result['stderr']}\n```"
                        else:
                            response = f"**Command failed:**\n```\n{result['stderr']}\n```"
                        self.chat_history.add_message("Orby", response)
                    else:
                        self.chat_history.add_message("Orby", "** Unsafe command blocked:** " + command)
                else:
                    self.chat_history.add_message("Orby", "**Terminal execution is disabled in configuration.**")
                self.input_widget.text = ""
                return
            elif prompt_lower.startswith('search:') or prompt_lower.startswith('find:'):
                if self.config.enable_online_search:
                    query = prompt[7:].strip()  # Remove 'search:' or 'find:'
                    self.chat_history.add_message("You", f"**SEARCHING:** {query}")
                    
                    # Create web searcher instance
                    web_searcher = WebSearcher()
                    results = web_searcher.search(query)
                    
                    if results:
                        response = f"**Search results for '{query}':**\n\n"
                        for i, result in enumerate(results[:3]):  # Show top 3 results
                            response += f"{i+1}. **{result['title']}**\n   {result['snippet'][:200]}...\n\n"
                    else:
                        response = f"**No search results found for:** {query}"
                    
                    self.chat_history.add_message("Orby", response)
                else:
                    self.chat_history.add_message("Orby", "**Online search is disabled in configuration.**")
                self.input_widget.text = ""
                return
            
            # Add user message to history
            self.chat_history.add_message("You", prompt)
            
            # Show thinking indicator
            self.thinking_container.visible = True
            self.chat_history.scroll_end(animate=True, speed=50)
            
            # Process with AI in a separate call to prevent UI blocking
            self._process_ai_response(prompt)
            
            # Clear input
            self.input_widget.text = ""
    
    def _process_ai_response(self, prompt: str):
        """Process AI response."""
        try:
            # Process with AI
            messages = [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # Get response from LLM with context enabled
            response = self.llm.chat_complete(messages, enable_context=True)
            
            # Add AI response to history
            self.chat_history.add_message("Orby", response)
            
            # If response contains code, display it in the code view
            if "```" in response:
                # Simple extraction of first code block
                parts = response.split("```")
                if len(parts) > 1:
                    code_block = parts[1].split('\n', 1)[-1]  # Remove language specifier line
                    if '\n' in code_block:
                        code_block = code_block.rsplit('\n', 1)[0]  # Remove closing ```
                    self.code_view.update_code(code_block)
                    self.code_view.display = True  # Show code panel if there's code
        
        except Exception as e:
            self.chat_history.add_message("Orby", f"**Error:** {str(e)}")
        finally:
            # Hide thinking indicator
            self.thinking_container.visible = False
            self.chat_history.scroll_end(animate=True, speed=50)
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
    
    def action_toggle_code_view(self) -> None:
        """Toggle the code view panel."""
        self.code_view.display = not self.code_view.display
    
    def on_descendant_focus(self, event: events.DescendantFocus) -> None:
        """Handle focus events to keep input focused."""
        pass
    
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text changes for input history."""
        pass

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