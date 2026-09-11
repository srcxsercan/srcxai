"""
Tab Completion System for SRCXAI Terminal
Provides intelligent tab completion for commands, files, and AI models
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import subprocess


class TabCompleter:
    """Tab completion system for SRCXAI terminal"""
    
    def __init__(self):
        self.commands = {
            'help': 'Show help information',
            'detect': 'Detect AI systems on the system',
            'install': 'Install AI tools and models',
            'chat': 'Start chat with AI model',
            'code': 'Generate or edit code',
            'ssh': 'SSH to remote system',
            'memory': 'Manage memory and context',
            'agent': 'Manage multi-agent system',
            'config': 'Manage configuration',
            'exit': 'Exit SRCXAI',
            'quit': 'Exit SRCXAI'
        }
        
        self.command_parameters = {
            'detect': ['--all', '--quick', '--install-missing'],
            'install': ['ollama', 'vllm', 'llamacpp', 'transformers', 'langchain'],
            'chat': ['--model', '--session', '--history'],
            'code': ['--language', '--file', '--edit'],
            'ssh': ['--connect', '--list', '--disconnect', '--exec'],
            'memory': ['--save', '--load', '--export', '--search'],
            'agent': ['--list', '--start', '--stop', '--status'],
            'config': ['--show', '--set', '--reset']
        }
        
        self.ai_models = []
        self.ssh_connections = []
        self.sessions = []
        
    def complete(self, text: str, state: int) -> Optional[str]:
        """Tab completion function"""
        if state == 0:
            self.matches = self._get_matches(text)
        
        try:
            return self.matches[state]
        except IndexError:
            return None
    
    def _get_matches(self, text: str) -> List[str]:
        """Get completion matches for text"""
        if not text:
            return list(self.commands.keys())
        
        # Split text into parts
        parts = text.split()
        
        if len(parts) == 1:
            # Complete command
            return [cmd for cmd in self.commands.keys() if cmd.startswith(text)]
        
        command = parts[0]
        current_part = parts[-1]
        
        # Complete based on command
        if command in self.command_parameters:
            params = self.command_parameters[command]
            matches = [p for p in params if p.startswith(current_part)]
            
            # Add file completions for certain commands
            if command in ['code', 'ssh']:
                file_matches = self._complete_files(current_part)
                matches.extend(file_matches)
            
            return matches
        
        # Complete AI models for chat command
        if command == 'chat' and '--model' in parts:
            return [model for model in self.ai_models if model.startswith(current_part)]
        
        # Complete SSH connections
        if command == 'ssh' and '--connect' in parts:
            return [conn for conn in self.ssh_connections if conn.startswith(current_part)]
        
        # Complete sessions
        if command in ['chat', 'memory'] and '--session' in parts:
            return [session for session in self.sessions if session.startswith(current_part)]
        
        # Default to file completion
        return self._complete_files(current_part)
    
    def _complete_files(self, text: str) -> List[str]:
        """Complete file paths"""
        if not text:
            return self._get_files_in_directory('.')
        
        # Check if it's a directory
        if os.path.isdir(text):
            return self._get_files_in_directory(text)
        
        # Get directory and prefix
        directory = os.path.dirname(text) or '.'
        prefix = os.path.basename(text)
        
        files = self._get_files_in_directory(directory)
        return [f for f in files if f.startswith(prefix)]
    
    def _get_files_in_directory(self, directory: str) -> List[str]:
        """Get files in directory with directory prefix"""
        try:
            files = []
            for item in os.listdir(directory):
                full_path = os.path.join(directory, item)
                if os.path.isdir(full_path):
                    files.append(item + '/')
                else:
                    files.append(item)
            return files
        except:
            return []
    
    def update_ai_models(self, models: List[str]):
        """Update available AI models"""
        self.ai_models = models
    
    def update_ssh_connections(self, connections: List[str]):
        """Update SSH connections"""
        self.ssh_connections = connections
    
    def update_sessions(self, sessions: List[str]):
        """Update available sessions"""
        self.sessions = sessions
    
    def get_command_help(self, command: str) -> Optional[str]:
        """Get help for a command"""
        if command in self.commands:
            help_text = f"{command}: {self.commands[command]}"
            if command in self.command_parameters:
                help_text += f"\nParameters: {', '.join(self.command_parameters[command])}"
            return help_text
        return None
    
    def get_all_commands(self) -> Dict[str, str]:
        """Get all commands and their descriptions"""
        return self.commands.copy()


class SmartCompleter:
    """Enhanced completer with context awareness"""
    
    def __init__(self, base_completer: TabCompleter):
        self.base_completer = base_completer
        self.context = {}
        self.history = []
    
    def set_context(self, key: str, value: Any):
        """Set context for completion"""
        self.context[key] = value
    
    def add_to_history(self, command: str):
        """Add command to history"""
        self.history.append(command)
        if len(self.history) > 100:  # Keep last 100 commands
            self.history.pop(0)
    
    def complete_with_context(self, text: str, state: int) -> Optional[str]:
        """Complete with context awareness"""
        # Check if we should complete from history
        if text.startswith('!'):
            history_text = text[1:]
            if state == 0:
                self.history_matches = [
                    '!' + cmd for cmd in self.history if cmd.startswith(history_text)
                ]
            try:
                return self.history_matches[state]
            except IndexError:
                return None
        
        # Check if we should complete from context
        if text.startswith('$'):
            context_text = text[1:]
            if state == 0:
                self.context_matches = [
                    '$' + key for key in self.context.keys() if key.startswith(context_text)
                ]
            try:
                return self.context_matches[state]
            except IndexError:
                return None
        
        # Default to base completer
        return self.base_completer.complete(text, state)
    
    def get_suggestions(self, text: str) -> List[str]:
        """Get completion suggestions without state"""
        suggestions = []
        
        # Get base completions
        for i in range(10):  # Get first 10 matches
            match = self.base_completer.complete(text, i)
            if match:
                suggestions.append(match)
        
        # Add history suggestions
        if text:
            history_suggestions = [cmd for cmd in self.history if text in cmd]
            suggestions.extend(history_suggestions[:5])
        
        return suggestions


def install_readline_completer(completer: TabCompleter):
    """Install tab completer for readline"""
    try:
        import readline
        readline.set_completer(completer.complete)
        readline.parse_and_bind('tab: complete')
        readline.set_completer_delims(' \t\n')
        return True
    except ImportError:
        return False


def install_prompt_toolkit_completer(completer: TabCompleter):
    """Install tab completer for prompt_toolkit (better experience)"""
    try:
        from prompt_toolkit import prompt
        from prompt_toolkit.completion import Completer, Completion
        from prompt_toolkit.document import Document
        
        class SRCXAICompleter(Completer):
            def __init__(self, tab_completer):
                self.tab_completer = tab_completer
            
            def get_completions(self, document: Document, complete_event):
                text = document.text_before_cursor
                matches = self.tab_completer._get_matches(text)
                
                for match in matches:
                    yield Completion(
                        match,
                        start_position=-len(text.split()[-1]) if text.split() else 0
                    )
        
        return SRCXAICompleter(completer)
    except ImportError:
        return None
