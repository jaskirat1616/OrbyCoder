"""Code command for Orby Coder."""
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.spinner import Spinner
from rich.live import Live
import os
from pathlib import Path
from orby_coder.core.llm_provider import LocalLLMProvider
from orby_coder.config.config_manager import ConfigManager
import time

console = Console()
app = typer.Typer()

def code_command(
    prompt: str = typer.Argument(..., help="The coding task or request"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="File to modify or create"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use for inference"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for generated code"),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream the response"),
    explain: bool = typer.Option(False, "--explain", "-e", help="Explain the generated code"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output")
):
    """Generate, modify, or explain code based on a prompt."""
    config_manager = ConfigManager()
    config = config_manager.get_current_config()
    llm = LocalLLMProvider(config)
    
    # Prepare the system prompt for code generation
    system_prompt = f"{config.system_prompt} You are an expert software developer. When providing code, always format it with proper syntax highlighting and include helpful comments."
    
    # If a file is specified, read its content and include it in the prompt
    file_content = ""
    if file and file.exists():
        with open(file, 'r') as f:
            file_content = f.read()
        user_prompt = f"Here is the current file content:\n```\n{file_content}\n```\n\n{prompt}\n\nIf modifying, please provide the complete updated file."
    else:
        user_prompt = prompt
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Show thinking indicator if verbose
    if verbose:
        spinner = Spinner("clock", "Orby Coder is working on your code...")
        with Live(spinner, console=console, refresh_per_second=10) as live:
            time.sleep(0.5)  # Brief pause to show thinking
            if stream:
                response = ""
                for chunk in llm.stream_chat(messages, model):
                    response += chunk
                live.update(Panel(Markdown(response), title="Code Generation Result"))
            else:
                response = llm.chat_complete(messages, model)
                live.update(Panel(Markdown(response), title="Code Generation Result"))
    else:
        if stream:
            console.print("[bold yellow]Orby Coder:[/bold yellow]\n", end="")
            response = ""
            for chunk in llm.stream_chat(messages, model):
                console.print(chunk, end="", markup=False)
                response += chunk
            console.print()  # New line after streaming
        else:
            response = llm.chat_complete(messages, model)
            
            # Try to detect and format code blocks
            if "```" in response:
                # This is a simple heuristic to format code blocks
                parts = response.split("```")
                has_code = False
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Odd indices are code blocks
                        has_code = True
                        # Extract language if specified
                        lines = part.strip().split('\n')
                        language = 'text'
                        if lines:
                            first_line = lines[0].strip()
                            if first_line and not first_line.startswith('```'):
                                language = first_line
                                code_block = '\n'.join(lines[1:])  # Skip the language line
                            else:
                                code_block = part.strip()
                            
                            syntax = Syntax(code_block, language, theme="monokai", line_numbers=True)
                            console.print(syntax)
                            console.print()  # Add space after code block
                    else:
                        # Regular text
                        if part.strip():
                            # Don't duplicate text if it's already shown as code
                            panel = Panel(Markdown(part.strip()), border_style="blue")
                            console.print(panel)
                
                # If no code blocks found, show everything as markdown
                if not has_code:
                    panel = Panel(Markdown(response), title="Code Generation Result")
                    console.print(panel)
            else:
                # If no code blocks detected, just print as markdown
                panel = Panel(Markdown(response), title="Code Generation Result")
                console.print(panel)
    
    # If explain flag is set, get explanation of the generated code
    if explain and response:
        console.print("\n[bold blue]Code Explanation:[/bold blue]")
        explanation_messages = [
            {"role": "system", "content": f"{config.system_prompt} Explain the following code in a clear and concise manner, focusing on how it works and what it does."},
            {"role": "user", "content": f"Explain this code:\n\n{response}"}
        ]
        
        if verbose:
            spinner = Spinner("clock", "Generating explanation...")
            with Live(spinner, console=console, refresh_per_second=10) as live:
                time.sleep(0.3)
                explanation = llm.chat_complete(explanation_messages, model)
                live.update(Panel(Markdown(explanation), title="Code Explanation"))
        else:
            explanation = llm.chat_complete(explanation_messages, model)
            panel = Panel(Markdown(explanation), title="Code Explanation")
            console.print(panel)
    
    # If output file is specified, write the response to it
    if output:
        with open(output, 'w') as f:
            f.write(response)
        console.print(f"\n[green]Code written to:[/green] {output}")
    
    # If input file was specified and no output file is specified, ask if user wants to save
    if file and not output:
        save_choice = typer.confirm("Do you want to save the changes to the original file?")
        if save_choice:
            with open(file, 'w') as f:
                f.write(response)
            console.print(f"[green]Changes saved to:[/green] {file}")