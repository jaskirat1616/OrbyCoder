"""Advanced utilities for Orby Coder - terminal execution, web search, IDE integration."""
import subprocess
import os
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
import requests
import pyperclip
import psutil
from git import Repo
import webbrowser
from urllib.parse import quote
from datetime import datetime

class TerminalExecutor:
    """Execute terminal commands with user permissions - Gemini CLI style tool."""
    
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
                cwd=cwd or Path.cwd(),
                timeout=30  # 30 second timeout for safety
            )
            
            return {
                'command': command,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode,
                'success': result.returncode == 0,
                'timestamp': datetime.now().isoformat()
            }
        except subprocess.TimeoutExpired:
            return {
                'command': command,
                'stdout': '',
                'stderr': 'Command timed out after 30 seconds',
                'return_code': -1,
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'command': command,
                'stdout': '',
                'stderr': str(e),
                'return_code': -1,
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    @staticmethod
    def safe_command(command: str) -> bool:
        """
        Check if a command is safe to execute - Gemini CLI style safety.
        
        Args:
            command: Command to check
            
        Returns:
            True if command is safe, False otherwise
        """
        # Dangerous commands that should never be executed
        dangerous_patterns = [
            'rm -rf /\??',
            'rm -r /\??',
            'rm - /\??',
            'dd if=/dev/',
            'dd of=/dev/',
            'mkfs',
            '>: /dev/',
            'mv ~',
            'chmod -R 777 /\??',
            'chown -R root /\??',
            ':(){:&};:'
        ]
        
        # Potentially dangerous commands that require extra caution
        cautious_patterns = [
            'rm -rf',
            'rm -r',
            'sudo',
            'shutdown',
            'reboot',
            'halt',
            'poweroff'
        ]
        
        command_lower = command.lower().strip()
        
        # Block explicitly dangerous commands
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return False
        
        # Warn about cautious commands (but don't block them)
        for pattern in cautious_patterns:
            if pattern in command_lower:
                # In a real implementation, we might want to prompt the user for confirmation
                pass
        
        return True


class WebSearcher:
    """Web search functionality for online information - Gemini CLI style tool."""
    
    @staticmethod
    def search(query: str, num_results: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Perform a web search for the given query - Gemini CLI style.
        
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
        timestamp = datetime.now().isoformat()
        
        # Simulate web search with more realistic results
        return [
            {
                "title": f"Search results for: {query}",
                "url": "https://example.com/search?q=" + quote(query),
                "snippet": f"This is a simulated search result for '{query}'. In a real implementation, this would show actual web search results from Google, DuckDuckGo, or other search engines.",
                "timestamp": timestamp
            },
            {
                "title": f"Related information about {query}",
                "url": "https://example.com/related/" + quote(query),
                "snippet": f"Additional context about '{query}' that could help answer your question. Gemini CLI would automatically use web search when it needs current information or isn't certain about a topic.",
                "timestamp": timestamp
            }
        ]


class IDEIntegration:
    """Integration with various IDEs like VSCode and Cursor - Gemini CLI style tool."""
    
    def __init__(self, config):
        self.config = config
    
    def open_file_in_vscode(self, file_path: str) -> bool:
        """
        Open a file in VSCode - Gemini CLI style integration.
        
        Args:
            file_path: Path to the file to open
            
        Returns:
            True if successful, False otherwise
        """
        try:
            vscode_path = self.config.ide_integration.vscode_path
            if not os.path.exists(vscode_path):
                # Try to find VSCode in common locations
                common_paths = [
                    '/usr/bin/code',
                    '/usr/local/bin/code',
                    '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code'
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        vscode_path = path
                        break
                else:
                    return False  # VSCode not found
            
            result = subprocess.run([vscode_path, file_path], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            return False
    
    def open_file_in_cursor(self, file_path: str) -> bool:
        """
        Open a file in Cursor - Gemini CLI style integration.
        
        Args:
            file_path: Path to the file to open
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor_path = self.config.ide_integration.cursor_path
            if not os.path.exists(cursor_path):
                # Try to find Cursor in common locations
                common_paths = [
                    '/usr/local/bin/cursor',
                    '/usr/bin/cursor',
                    '/Applications/Cursor.app/Contents/Resources/app/bin/cursor'
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        cursor_path = path
                        break
                else:
                    return False  # Cursor not found
            
            result = subprocess.run([cursor_path, file_path], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            return False
    
    def open_folder_in_vscode(self, folder_path: str) -> bool:
        """Open a folder in VSCode - Gemini CLI style."""
        return self.open_file_in_vscode(folder_path)  # VSCode can open folders the same way
    
    def open_folder_in_cursor(self, folder_path: str) -> bool:
        """Open a folder in Cursor - Gemini CLI style."""
        return self.open_file_in_cursor(folder_path)  # Cursor can open folders the same way


class ToolManager:
    """Manage all tools available to Orby - Gemini CLI style tool orchestration."""
    
    def __init__(self, config):
        self.config = config
        self.terminal_executor = TerminalExecutor()
        self.web_searcher = WebSearcher()
        self.ide_integration = IDEIntegration(config)
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific tool with parameters - Gemini CLI style tool usage.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            
        Returns:
            Tool execution result
        """
        timestamp = datetime.now().isoformat()
        
        try:
            if tool_name == "terminal_execution":
                command = params.get("command", "")
                if command and self.terminal_executor.safe_command(command):
                    result = self.terminal_executor.execute_command(command)
                    return {
                        "tool": "terminal_execution",
                        "params": params,
                        "result": result,
                        "timestamp": timestamp,
                        "success": True
                    }
                else:
                    return {
                        "tool": "terminal_execution",
                        "params": params,
                        "result": {"error": "Unsafe command blocked"},
                        "timestamp": timestamp,
                        "success": False
                    }
            
            elif tool_name == "web_search":
                query = params.get("query", "")
                if query:
                    results = self.web_searcher.search(query)
                    return {
                        "tool": "web_search",
                        "params": params,
                        "result": results,
                        "timestamp": timestamp,
                        "success": True
                    }
                else:
                    return {
                        "tool": "web_search",
                        "params": params,
                        "result": {"error": "No search query provided"},
                        "timestamp": timestamp,
                        "success": False
                    }
            
            elif tool_name == "ide_open_file":
                file_path = params.get("file_path", "")
                ide = params.get("ide", "vscode")
                if file_path and os.path.exists(file_path):
                    if ide == "cursor":
                        success = self.ide_integration.open_file_in_cursor(file_path)
                    else:
                        success = self.ide_integration.open_file_in_vscode(file_path)
                    
                    return {
                        "tool": "ide_open_file",
                        "params": params,
                        "result": {"success": success, "message": f"File opened in {ide}" if success else f"Failed to open file in {ide}"},
                        "timestamp": timestamp,
                        "success": success
                    }
                else:
                    return {
                        "tool": "ide_open_file",
                        "params": params,
                        "result": {"error": "File not found or invalid path"},
                        "timestamp": timestamp,
                        "success": False
                    }
            
            else:
                return {
                    "tool": tool_name,
                    "params": params,
                    "result": {"error": f"Unknown tool: {tool_name}"},
                    "timestamp": timestamp,
                    "success": False
                }
        
        except Exception as e:
            return {
                "tool": tool_name,
                "params": params,
                "result": {"error": str(e)},
                "timestamp": timestamp,
                "success": False
            }


def get_system_info() -> Dict[str, Any]:
    """Get system information - Gemini CLI style system awareness."""
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
        'disk_percent': (disk.used / disk.total) * 100,
        'timestamp': datetime.now().isoformat()
    }


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard - Gemini CLI style utility."""
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def paste_from_clipboard() -> str:
    """Paste text from clipboard - Gemini CLI style utility."""
    try:
        return pyperclip.paste()
    except Exception:
        return ""


def is_git_repo(path: str = ".") -> bool:
    """Check if the current directory is a git repository - Gemini CLI style awareness."""
    try:
        Repo(path)
        return True
    except:
        return False


def get_git_info(path: str = ".") -> Dict[str, Any]:
    """Get git repository information - Gemini CLI style project awareness."""
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
                'date': datetime.fromtimestamp(repo.head.commit.committed_date).isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': str(e), 'timestamp': datetime.now().isoformat()}