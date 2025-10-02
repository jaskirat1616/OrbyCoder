"""Chat command for Orby Coder."""
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from orby_coder.core.llm_provider import LocalLLMProvider
from orby_coder.config.config_manager import ConfigManager

console = Console()
app = typer.Typer()

def chat_command(
    prompt: Optional[str] = typer.Argument(None, help="The prompt to send to the AI"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use for inference"),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream the response")
):
    """Start an interactive chat session or process a single prompt."""
    config_manager = ConfigManager()
    config = config_manager.get_current_config()
    llm = LocalLLMProvider(config)
    
    # If no prompt provided, start interactive mode
    if not prompt:
        console.print("[bold green]Starting Orby Coder Chat...[/bold green]")
        console.print("Type 'exit' to quit, 'model' to change model, 'config' to see config\n")
        
        # Simple interactive chat loop
        while True:
            user_input = console.input("[bold blue]You:[/bold blue] ")
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("[bold green]Goodbye![/bold green]")
                break
            elif user_input.lower() == 'config':
                console.print(f"[yellow]Backend:[/yellow] {config.backend}")
                console.print(f"[yellow]Model:[/yellow] {config.default_model}")
                console.print(f"[yellow]System Prompt:[/yellow] {config.system_prompt[:50]}...")
                continue
            elif user_input.lower().startswith('model '):
                # Change model command
                new_model = user_input[6:].strip()  # Remove 'model ' prefix
                config.default_model = new_model
                console.print(f"[green]Model changed to:[/green] {new_model}")
                continue
            
            # Prepare messages for the AI
            messages = [
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            if stream:
                console.print("[bold yellow]Orby:[/bold yellow] ", end="")
                response = ""
                for chunk in llm.stream_chat(messages, model):
                    console.print(chunk, end="", markup=False)
                    response += chunk
                console.print()  # New line after streaming
            else:
                response = llm.chat_complete(messages, model)
                panel = Panel(Markdown(response), title="Orby's Response")
                console.print(panel)
    else:
        # Process single prompt
        messages = [
            {"role": "system", "content": config.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        if stream:
            console.print("[bold yellow]Orby:[/bold yellow] ", end="")
            response = ""
            for chunk in llm.stream_chat(messages, model):
                console.print(chunk, end="", markup=False)
                response += chunk
            console.print()  # New line after streaming
        else:
            response = llm.chat_complete(messages, model)
            panel = Panel(Markdown(response), title="Orby's Response")
            console.print(panel)