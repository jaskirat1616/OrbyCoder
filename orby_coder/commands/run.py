"""Run command for Orby Coder."""
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
import subprocess
import os
from pathlib import Path
from orby_coder.core.llm_provider import LocalLLMProvider
from orby_coder.config.config_manager import ConfigManager

console = Console()
app = typer.Typer()

def run_command(
    file: Path = typer.Argument(..., help="The file to run"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use for inference"),
    explain: bool = typer.Option(False, "--explain", "-e", help="Explain the code before running it"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Run with debugging output")
):
    """Execute a file and optionally explain or debug it."""
    config_manager = ConfigManager()
    config = config_manager.get_current_config()
    llm = LocalLLMProvider(config)
    
    if not file.exists():
        console.print(f"[red]Error:[/red] File '{file}' does not exist")
        raise typer.Exit(code=1)
    
    # Determine the command to run based on file extension
    ext = file.suffix.lower()
    
    if ext == '.py':
        cmd = ['python', str(file)]
    elif ext == '.js':
        cmd = ['node', str(file)]
    elif ext == '.ts':
        cmd = ['ts-node', str(file)]
    elif ext == '.sh':
        cmd = ['bash', str(file)]
    elif ext == '.go':
        cmd = ['go', 'run', str(file)]
    elif ext == '.rs':
        cmd = ['cargo', 'run', '--example', file.stem] if 'examples' in str(file) else ['cargo', 'run', '--bin', file.stem]
        # For Rust, we'll try a simpler approach if the above doesn't work
        if not os.path.exists('Cargo.toml'):
            console.print(f"[red]Error:[/red] Not in a Rust project (no Cargo.toml found)")
            raise typer.Exit(code=1)
    elif ext in ['.c', '.cpp', '.cc', '.cxx']:
        console.print(f"[red]Error:[/red] Compile and run commands not implemented for {ext} files yet")
        raise typer.Exit(code=1)
    else:
        console.print(f"[red]Error:[/red] Unsupported file extension: {ext}")
        raise typer.Exit(code=1)
    
    # If explain flag is set, first get the AI to explain the code
    if explain:
        console.print(f"[bold blue]Analyzing {file}...[/bold blue]")
        
        with open(file, 'r') as f:
            code_content = f.read()
        
        system_prompt = f"{config.system_prompt} You are an expert software developer. Provide a concise but comprehensive explanation of the code functionality."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Explain the following code:\n\n```\n{code_content}\n```"}
        ]
        
        explanation = llm.chat_complete(messages, model)
        
        panel = Panel(explanation, title=f"Explanation of {file.name}")
        console.print(panel)
    
    # Run the file
    console.print(f"[bold green]Running {file.name}...[/bold green]")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=file.parent
        )
        
        # Print stdout if there is any
        if result.stdout:
            console.print("\n[bold]Output:[/bold]")
            console.print(result.stdout)
        
        # Print stderr if there is any (in red)
        if result.stderr:
            console.print("\n[bold red]Errors:[/bold red]")
            console.print(result.stderr)
        
        # Show exit code
        if result.returncode != 0:
            console.print(f"\n[red]Process exited with code: {result.returncode}[/red]")
        else:
            console.print(f"\n[green]Process completed successfully[/green]")
            
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Command not found. Make sure {cmd[0]} is installed and in your PATH")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error running {file}:[/red] {str(e)}")
        raise typer.Exit(code=1)