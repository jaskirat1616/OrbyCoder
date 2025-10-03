"""Gemini CLI-style tools for Orby Coder."""
import os
import subprocess
import json
import platform
from typing import Dict, Any, Optional, List
from pathlib import Path
import requests
from datetime import datetime

class BaseTool:
    """Base class for all tools."""
    
    def __init__(self, name: str, display_name: str, description: str):
        self.name = name
        self.display_name = display_name
        self.description = description
    
    def validate_params(self, params: Dict[str, Any]) -> str | None:
        """Validate tool parameters. Returns error message or None if valid."""
        return None
    
    def should_confirm_execute(self, params: Dict[str, Any]) -> Dict[str, Any] | bool:
        """Check if tool execution should be confirmed. Returns confirmation details or False."""
        return False
    
    def execute(self, params: Dict[str, Any], signal: Optional[Any] = None) -> Dict[str, Any]:
        """Execute the tool. Returns tool result."""
        raise NotImplementedError()


class ShellTool(BaseTool):
    """Execute shell commands - Gemini CLI style."""
    
    def __init__(self):
        super().__init__(
            "run_shell_command",
            "Shell",
            "This tool executes a given shell command. Command can start background processes."
        )
    
    def validate_params(self, params: Dict[str, Any]) -> str | None:
        """Validate shell command parameters."""
        if "command" not in params:
            return "Missing required parameter: command"
        
        command = params["command"]
        if not isinstance(command, str) or not command.strip():
            return "Command must be a non-empty string"
        
        # Check for dangerous commands
        dangerous_commands = [
            "rm -rf /", "rm -r /", "format", "mkfs", 
            "dd if=", ":(){:&};:"
        ]
        
        command_lower = command.lower()
        for danger in dangerous_commands:
            if danger in command_lower:
                return f"Dangerous command blocked: {danger}"
        
        return None
    
    def should_confirm_execute(self, params: Dict[str, Any]) -> Dict[str, Any] | bool:
        """Check if shell command should be confirmed."""
        command = params.get("command", "")
        
        # Commands that typically require confirmation
        confirmation_commands = [
            "rm", "delete", "format", "mkfs", "chmod", "chown"
        ]
        
        command_lower = command.lower()
        for confirm_cmd in confirmation_commands:
            if confirm_cmd in command_lower:
                return {
                    "type": "exec",
                    "title": "Confirm Shell Command",
                    "command": command,
                    "message": f"This command may be destructive. Are you sure you want to execute: {command}?"
                }
        
        return False
    
    def execute(self, params: Dict[str, Any], signal: Optional[Any] = None) -> Dict[str, Any]:
        """Execute shell command."""
        command = params["command"]
        directory = params.get("directory", os.getcwd())
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=directory,
                timeout=30
            )
            
            # Format result for LLM
            llm_content = (
                f"Command: {command}\n"
                f"Directory: {directory}\n"
                f"Output: {result.stdout or '(empty)'}\n"
                f"Error: {result.stderr or '(none)'}\n"
                f"Exit Code: {result.returncode}\n"
                f"Signal: (none)\n"
                f"Background PIDs: (none)\n"
                f"Process Group PGID: {result.returncode}\n"
            )
            
            # Format result for display
            return_display = result.stdout or ""
            if result.stderr:
                return_display += f"\n[STDERR] {result.stderr}"
            
            return {
                "llmContent": llm_content,
                "returnDisplay": return_display
            }
            
        except subprocess.TimeoutExpired:
            return {
                "llmContent": f"Command timed out: {command}",
                "returnDisplay": "Command timed out after 30 seconds"
            }
        except Exception as e:
            return {
                "llmContent": f"Error executing command: {str(e)}",
                "returnDisplay": f"Error: {str(e)}"
            }


class WebSearchTool(BaseTool):
    """Web search tool - Gemini CLI style."""
    
    def __init__(self):
        super().__init__(
            "google_web_search",
            "GoogleSearch",
            "Performs a web search using Google Search and returns the results."
        )
    
    def validate_params(self, params: Dict[str, Any]) -> str | None:
        """Validate web search parameters."""
        if "query" not in params:
            return "Missing required parameter: query"
        
        query = params["query"]
        if not isinstance(query, str) or not query.strip():
            return "Query must be a non-empty string"
        
        return None
    
    def execute(self, params: Dict[str, Any], signal: Optional[Any] = None) -> Dict[str, Any]:
        """Execute web search."""
        query = params["query"]
        
        # In a real implementation, this would use Google Search API
        # For now, simulate search results
        timestamp = datetime.now().isoformat()
        
        search_results = [
            {
                "title": f"Search results for: {query}",
                "url": f"https://example.com/search?q={query}",
                "snippet": f"This is a simulated search result for '{query}'. In a real implementation, this would show actual web search results."
            },
            {
                "title": f"Related information about {query}",
                "url": f"https://example.com/related/{query}",
                "snippet": f"Additional context about '{query}' that could help answer your question."
            }
        ]
        
        # Format for LLM
        sources_text = "\n".join([
            f"[{i+1}] {result['title']} ({result['url']})"
            for i, result in enumerate(search_results)
        ])
        
        llm_content = (
            f"Web search results for \"{query}\":\n\n"
            f"{search_results[0]['snippet']}\n\n"
            f"Sources:\n{sources_text}"
        )
        
        return {
            "llmContent": llm_content,
            "returnDisplay": f"Search results for \"{query}\" returned.",
            "sources": search_results
        }


class ReadFileTool(BaseTool):
    """Read file tool - Gemini CLI style."""
    
    def __init__(self):
        super().__init__(
            "read_file",
            "ReadFile",
            "Reads and returns the content of a specified file."
        )
    
    def validate_params(self, params: Dict[str, Any]) -> str | None:
        """Validate read file parameters."""
        if "absolute_path" not in params:
            return "Missing required parameter: absolute_path"
        
        file_path = params["absolute_path"]
        if not isinstance(file_path, str) or not file_path.strip():
            return "File path must be a non-empty string"
        
        if not os.path.isabs(file_path):
            return "File path must be absolute"
        
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        if not os.path.isfile(file_path):
            return f"Path is not a file: {file_path}"
        
        return None
    
    def execute(self, params: Dict[str, Any], signal: Optional[Any] = None) -> Dict[str, Any]:
        """Read file content."""
        file_path = params["absolute_path"]
        offset = params.get("offset", 0)
        limit = params.get("limit")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Apply offset and limit if specified
            start_line = offset
            if limit:
                end_line = min(start_line + limit, len(lines))
                content_lines = lines[start_line:end_line]
            else:
                content_lines = lines[start_line:]
            
            content = ''.join(content_lines)
            
            # Check if content was truncated
            is_truncated = limit and len(lines) > (start_line + (limit or len(lines)))
            
            if is_truncated:
                llm_content = (
                    f"\nIMPORTANT: The file content has been truncated.\n"
                    f"Status: Showing lines {start_line+1}-{start_line+len(content_lines)} of {len(lines)} total lines.\n"
                    f"Action: To read more of the file, you can use the 'offset' and 'limit' parameters in a subsequent 'read_file' call.\n\n"
                    f"--- FILE CONTENT (truncated) ---\n{content}"
                )
            else:
                llm_content = content
            
            # Format for display
            return_display = f"Read file: {file_path}"
            if is_truncated:
                return_display += f" (lines {start_line+1}-{start_line+len(content_lines)})"
            
            return {
                "llmContent": llm_content,
                "returnDisplay": return_display
            }
            
        except Exception as e:
            return {
                "llmContent": f"Error reading file: {str(e)}",
                "returnDisplay": f"Error: {str(e)}"
            }


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.register_builtin_tools()
    
    def register_builtin_tools(self):
        """Register built-in tools."""
        self.register_tool(ShellTool())
        self.register_tool(WebSearchTool())
        self.register_tool(ReadFileTool())
    
    def register_tool(self, tool: BaseTool):
        """Register a tool."""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all registered tools."""
        schemas = []
        for tool in self.tools.values():
            schema = {
                "name": tool.name,
                "description": tool.description
            }
            schemas.append(schema)
        return schemas


# Global tool registry instance
tool_registry = ToolRegistry()