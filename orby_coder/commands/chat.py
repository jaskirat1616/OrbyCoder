"""Chat command for Orby Coder."""
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text
from orby_coder.core.llm_provider import LocalLLMProvider
from orby_coder.config.config_manager import ConfigManager
from orby_coder.utils.advanced import TerminalExecutor, WebSearcher, get_system_info
import threading
import time

console = Console()
app = typer.Typer()

def chat_command(
    prompt: Optional[str] = typer.Argument(None, help="The prompt to send to the AI"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use for inference"),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream the response"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", min=0.0, max=1.0, help="Set the temperature for the model (0.0-1.0)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
    enable_context: bool = typer.Option(True, "--context/--no-context", help="Enable enhanced context (web search, terminal commands)")
):
    """Start an interactive chat session or process a single prompt."""
    config_manager = ConfigManager()
    config = config_manager.get_current_config()
    
    # Update temperature if provided
    if temperature is not None:
        config.temperature = temperature
    
    llm = LocalLLMProvider(config)
    web_searcher = WebSearcher()
    
    # If no prompt provided, start interactive mode
    if not prompt:
        console.print("[bold green]Starting Orby Coder Chat...[/bold green]")
        console.print("Type 'help' for commands, 'exit' to quit\n")
        
        # Interactive chat loop with more Gemini CLI-like features
        while True:
            user_input = console.input("[bold blue]You:[/bold blue] ")
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("[bold green]Goodbye![/bold green]")
                break
            elif user_input.lower() == 'help':
                help_text = (
                    "[bold]Available Commands:[/bold]\n"
                    "• [green]help[/green] - Show this help message\n"
                    "• [green]models[/green] - List available models\n"
                    "• [green]model <name>[/green] - Change current model\n"
                    "• [green]config[/green] - Show current configuration\n"
                    "• [green]system[/green] - Show system information\n"
                    "• [green]temperature <value>[/green] - Set temperature (0.0-1.0)\n"
                    "• [green]clear[/green] - Clear screen\n"
                    "• [green]exit/quit/q[/green] - Exit the application\n"
                    "\n[bold]Advanced Usage:[/bold]\n"
                    "• [blue]execute: command[/blue] - Execute a terminal command\n"
                    "• [blue]search: query[/blue] - Search the web\n"
                    "Type any prompt to chat with Orby."
                )
                console.print(Panel(help_text, title="Help"))
                continue
            elif user_input.lower() == 'models':
                try:
                    models = llm.list_models()
                    if models:
                        models_list = "\n".join([f"• {model}" for model in models])
                        console.print(Panel(models_list, title="Available Models"))
                    else:
                        console.print("[yellow]No models found or backend not accessible.[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error listing models:[/red] {str(e)}")
                continue
            elif user_input.lower().startswith('model '):
                # Change the current model
                new_model = user_input[6:].strip()  # Remove 'model ' prefix
                if new_model:
                    # Validate that the model exists or at least has proper format
                    if len(new_model) > 0:
                        # Update the config with the new model
                        config.default_model = new_model
                        config_manager.save_config(config)
                        console.print(f"[green]Model changed to:[/green] {new_model}")
                        console.print(f"[blue]Current model:[/blue] {config.default_model}")
                    else:
                        console.print("[red]Please specify a model name.[/red]")
                        console.print("[yellow]Usage:[/yellow] model <model_name>")
                else:
                    console.print("[red]Please specify a model name.[/red]")
                    console.print("[yellow]Usage:[/yellow] model <model_name>")
                continue
            elif user_input.lower() == 'config':
                config_info = (
                    f"Backend: {config.backend}\n"
                    f"Default Model: {config.default_model}\n"
                    f"LM Studio URL: {config.lmstudio_base_url}\n"
                    f"Ollama URL: {config.ollama_base_url}\n"
                    f"Temperature: {config.temperature}\n"
                    f"Online Search: {config.enable_online_search}\n"
                    f"Terminal Execution: {config.enable_terminal_execution}\n"
                    f"System Prompt: {config.system_prompt[:50]}..."
                )
                console.print(Panel(config_info, title="Configuration"))
                continue
            elif user_input.lower() == 'system':
                sys_info = get_system_info()
                sys_text = (
                    f"CPU Usage: {sys_info['cpu_percent']}%\n"
                    f"Memory: {sys_info['memory_percent']:.1f}% ({sys_info['memory_available'] // (1024**3)}GB free)\n"
                    f"Disk: {sys_info['disk_percent']:.1f}% used\n"
                )
                console.print(Panel(sys_text, title="System Information"))
                continue
            elif user_input.lower().startswith('temperature '):
                try:
                    temp_str = user_input.split(' ', 1)[1]
                    temp_value = float(temp_str)
                    if 0.0 <= temp_value <= 1.0:
                        config.temperature = temp_value
                        # Update the config manager as well
                        config_manager.save_config(config)
                        console.print(f"[green]Temperature set to:[/green] {temp_value}")
                    else:
                        console.print("[red]Temperature must be between 0.0 and 1.0[/red]")
                except (ValueError, IndexError):
                    console.print("[red]Invalid temperature command. Use: temperature <value>[/red]")
                continue
            elif user_input.lower() in ['clear', 'cls']:
                console.clear()
                continue
            
            # Check for special commands
            user_input_lower = user_input.lower()
            if user_input_lower.startswith('execute:') or user_input_lower.startswith('run:'):
                if config.enable_terminal_execution:
                    command = user_input[8:].strip()  # Remove 'execute:' or 'run:'
                    if TerminalExecutor.safe_command(command):
                        console.print(f"[bold yellow]Executing:[/bold yellow] {command}")
                        result = TerminalExecutor.execute_command(command)
                        if result['success']:
                            console.print(f"[green]Command succeeded:[/green]")
                            if result['stdout']:
                                console.print(result['stdout'])
                            if result['stderr']:
                                console.print(f"[red]Stderr:[/red] {result['stderr']}")
                        else:
                            console.print(f"[red]Command failed:[/red] {result['stderr']}")
                    else:
                        console.print(f"[red]Unsafe command blocked:[/red] {command}")
                else:
                    console.print("[red]Terminal execution is disabled in configuration.[/red]")
                continue
            elif user_input_lower.startswith('search:') or user_input_lower.startswith('find:'):
                if config.enable_online_search:
                    query = user_input[7:].strip()  # Remove 'search:' or 'find:'
                    console.print(f"[bold yellow]Searching:[/bold yellow] {query}")
                    results = web_searcher.search(query)
                    if results:
                        result_text = f"Results for '{query}':\n"
                        for i, result in enumerate(results[:3]):  # Show top 3 results
                            result_text += f"{i+1}. {result['title']}\n   {result['snippet'][:100]}...\n"
                        console.print(Panel(result_text, title="Web Search Results"))
                    else:
                        console.print(f"[red]No search results found for:[/red] {query}")
                else:
                    console.print("[red]Online search is disabled in configuration.[/red]")
                continue
            
            # Prepare messages for the AI
            messages = [
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Show a thinking indicator before processing
            if verbose:
                spinner = Spinner("clock", "Orby is thinking...")
                with Live(spinner, console=console, refresh_per_second=10) as live:
                    time.sleep(0.5)  # Brief pause to show thinking
                    try:
                        if stream:
                            response = ""
                            for chunk in llm.stream_chat(messages, model, enable_context):
                                response += chunk
                            live.update(Panel(Markdown(response), title="Orby's Response"))
                            time.sleep(0.1)  # Brief pause before showing response
                        else:
                            response = llm.chat_complete(messages, model, enable_context)
                            live.update(Panel(Markdown(response), title="Orby's Response"))
                            time.sleep(0.1)  # Brief pause before showing response
                    except Exception as e:
                        error_msg = str(e)
                        live.update(Panel(f"[red]Error:[/red] {error_msg}", title="Error"))
                        time.sleep(2)  # Show error for 2 seconds
                        continue
            else:
                try:
                    if stream:
                        console.print("[bold yellow]Orby:[/bold yellow] ", end="")
                        response = ""
                        for chunk in llm.stream_chat(messages, model, enable_context):
                            console.print(chunk, end="", markup=False)
                            response += chunk
                        console.print()  # New line after streaming
                    else:
                        response = llm.chat_complete(messages, model, enable_context)
                        panel = Panel(Markdown(response), title="Orby's Response")
                        console.print(panel)
                except Exception as e:
                    error_msg = str(e)
                    console.print(f"[red]Error:[/red] {error_msg}")
                    if "not found" in error_msg.lower() and "ollama pull" in error_msg:
                        console.print("[yellow]Tip:[/yellow] Run the suggested command to download the model first.")
                    continue
    else:
        # Process single prompt
        messages = [
            {"role": "system", "content": config.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        if verbose:
            spinner = Spinner("clock", "Orby is thinking...")
            with Live(spinner, console=console, refresh_per_second=10) as live:
                time.sleep(0.5)  # Brief pause to show thinking
                try:
                    if stream:
                        response = ""
                        for chunk in llm.stream_chat(messages, model, enable_context):
                            response += chunk
                        live.update(Panel(Markdown(response), title="Orby's Response"))
                    else:
                        response = llm.chat_complete(messages, model, enable_context)
                        live.update(Panel(Markdown(response), title="Orby's Response"))
                except Exception as e:
                    error_msg = str(e)
                    live.update(Panel(f"[red]Error:[/red] {error_msg}", title="Error"))
                    return
        else:
            try:
                if stream:
                    console.print("[bold yellow]Orby:[/bold yellow] ", end="")
                    response = ""
                    for chunk in llm.stream_chat(messages, model, enable_context):
                        console.print(chunk, end="", markup=False)
                        response += chunk
                    console.print()  # New line after streaming
                else:
                    response = llm.chat_complete(messages, model, enable_context)
                    panel = Panel(Markdown(response), title="Orby's Response")
                    console.print(panel)
            except Exception as e:
                error_msg = str(e)
                console.print(f"[red]Error:[/red] {error_msg}")
                if "not found" in error_msg.lower() and "ollama pull" in error_msg:
                    console.print("[yellow]Tip:[/yellow] Run the suggested command to download the model first.")
                return