"""Advanced utilities for Orby Coder - terminal execution, web search, IDE integration."""
import subprocess
import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
import requests
import pyperclip
import psutil
from git import Repo
import webbrowser
from urllib.parse import quote

class TerminalExecutor:
    """Execute terminal commands with user permissions."""
    
    @staticmethod
    def execute_command(command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a command in the terminal with the current user's permissions.
        
        Args:
            command: Command to execute
            cwd: Working directory (optional)
            
        Returns:
            Dictionary with 'stdout', 'stderr', 'return_code', 'command'
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd or Path.cwd()
            )
            
            return {
                'command': command,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode,
                'success': result.returncode == 0
            }
        except Exception as e:
            return {
                'command': command,
                'stdout': '',
                'stderr': str(e),
                'return_code': -1,
                'success': False
            }
    
    @staticmethod
    def safe_command(command: str) -> bool:
        """
        Check if a command is safe to execute.
        
        Args:
            command: Command to check
            
        Returns:
            True if command is safe, False otherwise
        """
        dangerous_patterns = [
            'rm -rf',
            'rm -r',
            'rm -',
            'dd if=',
            'mkfs',
            '> /dev/',
            '>/dev/',
            'mv ~',
            'chmod -R 777 /',
            'chown -R root',
            ':(){:&};:'
        ]
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return False
        
        return True


class WebSearcher:
    """Web search functionality for online information."""
    
    @staticmethod
    def search(query: str, num_results: int = 5) -> Optional[list]:
        """
        Perform a web search for the given query.
        In a production implementation, you would use a search API like Google Custom Search,
        DuckDuckGo, or similar. For now, this is a placeholder implementation.
        
        Args:
            query: Search query
            num_results: Number of results to return (default 5)
            
        Returns:
            List of search results or None if search fails
        """
        # Placeholder implementation - in a real version you would use an API
        # such as Google Custom Search, SerpAPI, DuckDuckGo API, etc.
        print(f"[WEB SEARCH SIMULATION]: {query}")
        
        # For now, return a placeholder response
        return [
            {"title": f"Search result for: {query}", "url": "https://example.com", "snippet": f"Placeholder search result for query: {query}"}
        ]


class IDEIntegration:
    """Integration with various IDEs like VSCode and Cursor."""
    
    def __init__(self, config):
        self.config = config
    
    def open_file_in_vscode(self, file_path: str) -> bool:
        """
        Open a file in VSCode.
        
        Args:
            file_path: Path to the file to open
            
        Returns:
            True if successful, False otherwise
        """
        try:
            vscode_path = self.config.ide_integration.vscode_path
            if not os.path.exists(vscode_path) and os.path.exists('/usr/bin/code'):
                vscode_path = '/usr/bin/code'
            elif not os.path.exists(vscode_path) and os.path.exists('/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code'):
                vscode_path = '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code'
            
            result = subprocess.run([vscode_path, file_path], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            # Try common locations for VSCode
            common_paths = [
                '/usr/bin/code',
                '/usr/local/bin/code',
                '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code'
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    try:
                        subprocess.run([path, file_path], capture_output=True, text=True)
                        return True
                    except Exception:
                        continue
            
            return False
    
    def open_file_in_cursor(self, file_path: str) -> bool:
        """
        Open a file in Cursor.
        
        Args:
            file_path: Path to the file to open
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor_path = self.config.ide_integration.cursor_path
            result = subprocess.run([cursor_path, file_path], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            # Try common locations for Cursor
            common_paths = [
                '/usr/local/bin/cursor',
                '/usr/bin/cursor',
                '/Applications/Cursor.app/Contents/Resources/app/bin/cursor'
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    try:
                        subprocess.run([path, file_path], capture_output=True, text=True)
                        return True
                    except Exception:
                        continue
            
            return False
    
    def open_folder_in_vscode(self, folder_path: str) -> bool:
        """Open a folder in VSCode."""
        try:
            vscode_path = self.config.ide_integration.vscode_path
            if not os.path.exists(vscode_path) and os.path.exists('/usr/bin/code'):
                vscode_path = '/usr/bin/code'
            elif not os.path.exists(vscode_path) and os.path.exists('/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code'):
                vscode_path = '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code'
            
            result = subprocess.run([vscode_path, folder_path], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            # Try common locations
            common_paths = [
                '/usr/bin/code',
                '/usr/local/bin/code',
                '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code'
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    try:
                        subprocess.run([path, folder_path], capture_output=True, text=True)
                        return True
                    except Exception:
                        continue
            
            return False
    
    def open_folder_in_cursor(self, folder_path: str) -> bool:
        """Open a folder in Cursor."""
        try:
            cursor_path = self.config.ide_integration.cursor_path
            result = subprocess.run([cursor_path, folder_path], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            # Try common locations
            common_paths = [
                '/usr/local/bin/cursor',
                '/usr/bin/cursor',
                '/Applications/Cursor.app/Contents/Resources/app/bin/cursor'
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    try:
                        subprocess.run([path, folder_path], capture_output=True, text=True)
                        return True
                    except Exception:
                        continue
            
            return False


def get_system_info() -> Dict[str, Any]:
    """Get system information."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu_percent': cpu_percent,
        'memory_total': memory.total,
        'memory_available': memory.available,
        'memory_percent': memory.percent,
        'disk_total': disk.total,
        'disk_used': disk.used,
        'disk_free': disk.free,
        'disk_percent': (disk.used / disk.total) * 100
    }


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard."""
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def paste_from_clipboard() -> str:
    """Paste text from clipboard."""
    try:
        return pyperclip.paste()
    except Exception:
        return ""


def is_git_repo(path: str = ".") -> bool:
    """Check if the current directory is a git repository."""
    try:
        Repo(path)
        return True
    except:
        return False


def get_git_info(path: str = ".") -> Dict[str, Any]:
    """Get git repository information."""
    try:
        repo = Repo(path)
        return {
            'active_branch': repo.active_branch.name,
            'is_dirty': repo.is_dirty(),
            'uncommitted_files': [item.a_path for item in repo.index.diff(None)],
            'remote_url': list(repo.remotes)[0].url if repo.remotes else None,
            'latest_commit': {
                'hash': repo.head.commit.hexsha,
                'message': repo.head.commit.message.strip(),
                'author': repo.head.commit.author.name,
                'date': repo.head.commit.committed_date
            }
        }
    except Exception as e:
        return {'error': str(e)}