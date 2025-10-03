"""Main entry point for Orby Coder CLI."""
import typer
from typing import Optional
import sys

# Import our modules
from orby_coder.commands.chat import chat_command
from orby_coder.commands.code import code_command
from orby_coder.commands.run import run_command
from orby_coder.commands.ui import ui_command
from orby_coder.config.config_manager import ConfigManager
from orby_coder.ui.logo import print_logo

app = typer.Typer(
    name="orby",
    help="Orby Coder - Open Source AI CLI for coding and development",
    add_completion=False,
)

# Add commands to the app
app.command(name="chat", help="Start an interactive chat session or process a single prompt.")(chat_command)
app.command(name="code", help="Generate, modify, or explain code based on a prompt.")(code_command)
app.command(name="run", help="Execute a file and optionally explain or debug it.")(run_command)
app.command(name="ui", help="Launch the Textual-based interactive UI.")(ui_command)

def print_welcome_message():
    """Print a welcome message with setup instructions."""
    print("\n📝 Welcome to Orby Coder!")
    print("   To get started, you'll need to install a local AI model:")
    print("   • For Ollama: Install from https://ollama.com and run 'ollama pull llama3.2'")
    print("   • For LM Studio: Install from https://lmstudio.ai and load a model")
    print("\n💡 Tip: Run 'orby ui' for the Gemini CLI-like interface")
    print("   Run 'orby chat --help' for chat command options")
    print("   Run 'orby code --help' for code generation options")
    print("   Run 'orby run --help' for file execution options")
    print("\n🔧 Configuration: ~/.orby/config.json")
    print("   Docs: https://github.com/jaskirat1616/OrbyCoder")
    print()

def main():
    """Main entry point for the CLI."""
    # Print logo on startup (for non-UI commands and when no specific command is given)
    if len(sys.argv) == 1:
        print_logo()
        print_welcome_message()
        # Show help when no arguments are provided
        app()
    else:
        # Initialize config
        config = ConfigManager()
        
        # Print logo for non-UI commands only
        if len(sys.argv) > 1 and sys.argv[1] not in ['ui', '--help', '--version', 'help']:
            print_logo()
        
        # Run the Typer app
        try:
            app()
        except KeyboardInterrupt:
            typer.echo("\nGoodbye! 👋")
            sys.exit(0)

if __name__ == "__main__":
    main()