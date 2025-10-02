"""Utility functions for Orby Coder."""
import os
from pathlib import Path
from typing import List, Optional
import subprocess

def find_project_root(marker_files: Optional[List[str]] = None) -> Optional[Path]:
    """
    Find the project root by looking for common marker files/directories.
    
    Args:
        marker_files: List of files/directories that indicate project root.
                     Defaults to common markers like 'pyproject.toml', 'setup.py', etc.
    
    Returns:
        Path to project root if found, otherwise None
    """
    if marker_files is None:
        marker_files = [
            'pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt',
            'Pipfile', 'poetry.lock', '.git', 'package.json', 'Cargo.toml',
            'go.mod', 'Makefile', 'CMakeLists.txt'
        ]
    
    current_path = Path.cwd().resolve()
    
    # Start from current directory and go up
    for parent in [current_path] + list(current_path.parents):
        for marker in marker_files:
            if (parent / marker).exists():
                return parent
    
    return None

def get_git_root() -> Optional[Path]:
    """
    Get the root of the git repository if in one.
    
    Returns:
        Path to git root if in a git repo, otherwise None
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path.cwd()
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def is_git_repo(path: Path) -> bool:
    """
    Check if the given path is inside a git repository.
    
    Args:
        path: Path to check
    
    Returns:
        True if path is inside a git repo, False otherwise
    """
    try:
        result = subprocess.run(
            ['git', '-C', str(path), 'rev-parse', '--git-dir'],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_file_encoding(file_path: Path) -> str:
    """
    Detect the encoding of a file.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        Detected encoding as a string
    """
    import chardet
    
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # Read first 10KB to detect encoding
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'

def format_code_block(code: str, language: str = 'python') -> str:
    """
    Format a code block with proper syntax markers.
    
    Args:
        code: The code to format
        language: The programming language for syntax highlighting
        
    Returns:
        Formatted code block with markdown syntax
    """
    return f"```{language}\n{code}\n```"

def sanitize_model_name(model_name: str) -> str:
    """
    Sanitize a model name to be safe for use in file systems and URLs.
    
    Args:
        model_name: The model name to sanitize
        
    Returns:
        Sanitized model name
    """
    # Remove or replace invalid characters
    sanitized = model_name.replace('/', '_').replace('\\', '_').replace(' ', '_')
    # Remove other potentially problematic characters
    for char in '<>:"|?*':
        sanitized = sanitized.replace(char, '_')
    return sanitized.strip()

def validate_model_exists(model_name: str, backend: str) -> bool:
    """
    Validate that a model exists for the given backend.
    
    Args:
        model_name: Name of the model to validate
        backend: Backend to check against ('ollama' or 'lmstudio')
        
    Returns:
        True if model exists or can be assumed to exist, False otherwise
    """
    # This is a simplified check. In a full implementation, this would
    # actually query the backend to see if the model exists.
    if not model_name or not backend:
        return False
    
    # For now, just check that the model name is not empty
    return len(model_name.strip()) > 0