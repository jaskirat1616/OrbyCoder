"""Run command for Orby Coder."""
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.spinner import Spinner
from rich.live import Live
import subprocess
import os
import time
from pathlib import Path
from orby_coder.core.llm_provider import LocalLLMProvider
from orby_coder.config.config_manager import ConfigManager

console = Console()
app = typer.Typer()

def run_command(
    file: Path = typer.Argument(..., help="The file to run"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use for inference"),
    explain: bool = typer.Option(False, "--explain", "-e", help="Explain the code before running it"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Run with debugging output"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
    analyze: bool = typer.Option(False, "--analyze", "-a", help="Analyze code for potential issues")
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
        # Check if we're in a Cargo project
        cargo_toml = file.parent if file.name.endswith('.rs') else Path.cwd()
        while cargo_toml != cargo_toml.parent:
            if (cargo_toml / 'Cargo.toml').exists():
                cmd = ['cargo', 'run', '--bin', file.stem]
                break
            cargo_toml = cargo_toml.parent
        else:
            # Not in a cargo project, just try rustc
            console.print(f"[red]Error:[/red] Not in a Rust project (no Cargo.toml found)")
            raise typer.Exit(code=1)
    elif ext in ['.c', '.cpp', '.cc', '.cxx']:
        # For C/C++, compile first then run
        executable = file.with_suffix('')
        compile_cmd = ['gcc' if ext == '.c' else 'g++', '-o', str(executable), str(file)]
        try:
            result = subprocess.run(compile_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                console.print(f"[red]Compilation failed:[/red]\n{result.stderr}")
                raise typer.Exit(code=1)
            cmd = [str(executable)]
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] gcc/g++ not found. Please install a C/C++ compiler.")
            raise typer.Exit(code=1)
    else:
        console.print(f"[red]Error:[/red] Unsupported file extension: {ext}")
        console.print(f"[blue]Supported extensions:[/blue] .py, .js, .ts, .sh, .go, .rs, .c, .cpp, .cc, .cxx")
        raise typer.Exit(code=1)
    
    # If analyze flag is set, get AI to analyze the code for potential issues
    if analyze:
        console.print(f"[bold blue]Analyzing {file.name} for potential issues...[/bold blue]")
        
        with open(file, 'r') as f:
            code_content = f.read()
        
        system_prompt = f"{config.system_prompt} Analyze the following code for potential issues, bugs, performance problems, or improvements. Be specific and provide actionable feedback."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this code for potential issues:\n\n```\n{code_content}\n```"}
        ]
        
        if verbose:
            spinner = Spinner("clock", "Analyzing code...")
            with Live(spinner, console=console, refresh_per_second=10) as live:
                time.sleep(0.3)
                analysis = llm.chat_complete(messages, model)
                live.update(Panel(Markdown(analysis), title=f"Analysis of {file.name}"))
        else:
            analysis = llm.chat_complete(messages, model)
            panel = Panel(Markdown(analysis), title=f"Analysis of {file.name}")
            console.print(panel)
    
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
        
        if verbose:
            spinner = Spinner("clock", "Generating explanation...")
            with Live(spinner, console=console, refresh_per_second=10) as live:
                time.sleep(0.3)
                explanation = llm.chat_complete(messages, model)
                live.update(Panel(Markdown(explanation), title=f"Explanation of {file.name}"))
        else:
            explanation = llm.chat_complete(messages, model)
            panel = Panel(Markdown(explanation), title=f"Explanation of {file.name}")
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
    
    # After execution, ask the user if they want AI analysis of the output
    if result.stdout or result.stderr:
        analyze_output = typer.confirm("Would you like AI analysis of the execution output?")
        if analyze_output:
            output_content = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}" if result.stdout or result.stderr else "No output"
            
            system_prompt = f"{config.system_prompt} Analyze the following program output for correctness, errors, or insights."
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this program output:\n\n{output_content}"}
            ]
            
            if verbose:
                spinner = Spinner("clock", "Analyzing output...")
                with Live(spinner, console=console, refresh_per_second=10) as live:
                    time.sleep(0.3)
                    analysis = llm.chat_complete(messages, model)
                    live.update(Panel(Markdown(analysis), title="Output Analysis"))
            else:
                analysis = llm.chat_complete(messages, model)
                panel = Panel(Markdown(analysis), title="Output Analysis")
                console.print(panel)