"""
Main CLI Interface for SRCXAI
Comprehensive command-line interface with all features
"""

import os
import sys
import argparse
from typing import Optional
from pathlib import Path

from .config import SRCXAIConfig, get_default_config
from .ai_detector import AIDetector
from .memory import MemoryManager
from .ssh_manager import SSHManager
from .multi_agent import MultiAgentCoordinator, CoderAgent, AnalystAgent, ExecutorAgent
from .tab_completion import TabCompleter, SmartCompleter, install_readline_completer
from .error_handler import ErrorHandler, setup_global_error_handling


class SRCXAICLI:
    """Main CLI interface for SRCXAI"""
    
    def __init__(self):
        self.config = get_default_config()
        self.config.save()
        
        self.error_handler = setup_global_error_handling()
        self.memory = MemoryManager(self.config.memory_db)
        self.ai_detector = AIDetector()
        self.ssh_manager = SSHManager()
        self.coordinator = MultiAgentCoordinator()
        
        self.tab_completer = TabCompleter()
        self.smart_completer = SmartCompleter(self.tab_completer)
        
        self.current_session = self.memory.create_session_id()
        self._setup_agents()
        self._auto_detect_ai()
    
    def _setup_agents(self):
        """Setup default agents"""
        # Register specialized agents
        coder = CoderAgent(self.config.models['gpt-4'].name, self.memory)
        analyst = AnalystAgent(self.config.models['claude-3'].name, self.memory)
        executor = ExecutorAgent(self.config.models['local-llama'].name, self.memory)
        
        # Register with coordinator
        self.coordinator.register_agent('coder', 'code_generation', 'gpt-4', coder.capabilities)
        self.coordinator.register_agent('analyst', 'analysis', 'claude-3', analyst.capabilities)
        self.coordinator.register_agent('executor', 'execution', 'local-llama', executor.capabilities)
        
        # Store specialized agents for direct access
        self.coder_agent = coder
        self.analyst_agent = analyst
        self.executor_agent = executor
    
    def _auto_detect_ai(self):
        """Auto-detect AI systems"""
        if self.config.auto_detect_ai:
            print("🔍 Detecting AI systems...")
            detection_results = self.ai_detector.detect_all()
            
            for system, info in detection_results.items():
                status = "✅ Installed" if info['installed'] else "❌ Not installed"
                version = f" ({info['version']})" if info['version'] else ""
                print(f"  {system}: {status}{version}")
            
            # Update tab completer with available models
            models = self.ai_detector.get_available_models()
            self.tab_completer.update_ai_models(models)
            
            # Auto-install if enabled
            if self.config.auto_install_tools:
                print("\n📦 Checking for missing tools...")
                self.ai_detector.auto_install_missing()
    
    def start_interactive_mode(self):
        """Start interactive CLI mode"""
        # Install tab completion
        install_readline_completer(self.tab_completer)
        
        print("🤖 SRCXAI Multi-Agent System v2.0")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("Type 'help' for available commands or 'exit' to quit")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        self.coordinator.start(num_workers=3)
        
        try:
            while True:
                try:
                    user_input = input("SRCXAI> ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ['exit', 'quit']:
                        print("👋 Shutting down SRCXAI...")
                        break
                    
                    # Add to history
                    self.smart_completer.add_to_history(user_input)
                    
                    # Process command
                    self.process_command(user_input)
                    
                except KeyboardInterrupt:
                    print("\n⚠️  Use 'exit' to quit")
                except EOFError:
                    print("\n👋 Shutting down SRCXAI...")
                    break
                    
        finally:
            self.coordinator.stop()
            self.memory.close()
            self.ssh_manager.disconnect_all()
    
    def process_command(self, command: str):
        """Process a command"""
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        try:
            if cmd == 'help':
                self.show_help()
            elif cmd == 'detect':
                self.handle_detect(args)
            elif cmd == 'install':
                self.handle_install(args)
            elif cmd == 'chat':
                self.handle_chat(args)
            elif cmd == 'code':
                self.handle_code(args)
            elif cmd == 'ssh':
                self.handle_ssh(args)
            elif cmd == 'memory':
                self.handle_memory(args)
            elif cmd == 'agent':
                self.handle_agent(args)
            elif cmd == 'config':
                self.handle_config(args)
            else:
                print(f"❓ Unknown command: {cmd}")
                print("Type 'help' for available commands")
                
        except Exception as e:
            self.error_handler.handle_error(e, {'command': cmd, 'args': args})
            print(f"❌ Error: {e}")
    
    def show_help(self):
        """Show help information"""
        print("📖 Available Commands:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for cmd, description in self.tab_completer.get_all_commands().items():
            print(f"  {cmd:12} - {description}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("\n💡 Tips:")
        print("  - Press TAB for command completion")
        print("  - Use !command to search command history")
        print("  - Use $variable to access context variables")
    
    def handle_detect(self, args):
        """Handle AI detection command"""
        if '--all' in args or not args:
            results = self.ai_detector.detect_all()
            print("\n🔍 AI Systems Detection Results:")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            for system, info in results.items():
                status = "✅" if info['installed'] else "❌"
                version = f" ({info['version']})" if info['version'] else ""
                print(f"  {status} {system}{version}")
        elif '--quick' in args:
            print("🔍 Quick detection...")
            results = self.ai_detector.detect_all()
            installed = [k for k, v in results.items() if v['installed']]
            print(f"✅ Found {len(installed)} installed AI systems")
        elif '--install-missing' in args:
            print("📦 Installing missing AI tools...")
            results = self.ai_detector.auto_install_missing()
            for tool, success in results.items():
                status = "✅" if success else "❌"
                print(f"  {status} {tool}")
    
    def handle_install(self, args):
        """Handle installation command"""
        if not args:
            print("📦 Available tools to install:")
            print("  ollama, vllm, llamacpp, transformers, langchain")
            print("Usage: install <tool_name>")
            return
        
        tool = args[0]
        results = self.ai_detector.auto_install_missing([tool])
        
        for tool_name, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {tool_name}: {'Installed' if success else 'Failed'}")
    
    def handle_chat(self, args):
        """Handle chat command"""
        model = None
        if '--model' in args:
            idx = args.index('--model')
            if idx + 1 < len(args):
                model = args[idx + 1]
        
        print(f"💬 Starting chat session (model: {model or 'default'})")
        print("Type '/quit' to end chat session\n")
        
        while True:
            try:
                user_message = input("You> ").strip()
                
                if user_message.lower() in ['/quit', '/exit']:
                    print("👋 Ending chat session")
                    break
                
                if not user_message:
                    continue
                
                # Store in memory
                self.memory.add_conversation_message(
                    self.current_session, 'user', user_message
                )
                
                # Get response from AI (placeholder - would integrate with actual AI)
                response = self._get_ai_response(user_message, model)
                
                print(f"AI> {response}")
                
                # Store response in memory
                self.memory.add_conversation_message(
                    self.current_session, 'assistant', response
                )
                
            except KeyboardInterrupt:
                print("\n👋 Ending chat session")
                break
    
    def _get_ai_response(self, message: str, model: Optional[str]) -> str:
        """Get AI response (placeholder - integrate with actual AI models)"""
        # This would integrate with actual AI models based on configuration
        # For now, return a placeholder response
        return f"I understand you said: {message}. (AI integration would be here)"
    
    def handle_code(self, args):
        """Handle code generation/editing command"""
        if '--language' in args:
            idx = args.index('--language')
            language = args[idx + 1] if idx + 1 < len(args) else 'python'
        else:
            language = 'python'
        
        if '--file' in args:
            idx = args.index('--file')
            file_path = args[idx + 1] if idx + 1 < len(args) else None
        else:
            file_path = None
        
        print(f"💻 Code mode (language: {language})")
        print("Describe the code you want to generate or edit:")
        
        description = input("Description> ").strip()
        
        if description:
            code = self.coder_agent.write_code(description, language)
            print("\n📝 Generated Code:")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(code)
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            if file_path:
                self.executor_agent.execute_command(f"cat > {file_path} << 'EOF'\n{code}\nEOF")
                print(f"✅ Code written to {file_path}")
    
    def handle_ssh(self, args):
        """Handle SSH commands"""
        if '--list' in args:
            connections = self.ssh_manager.get_active_connections()
            if connections:
                print("🔗 Active SSH Connections:")
                for conn in connections:
                    print(f"  - {conn}")
            else:
                print("No active SSH connections")
        
        elif '--connect' in args:
            idx = args.index('--connect')
            if idx + 1 < len(args):
                # Parse connection string (user@host:port or alias)
                conn_str = args[idx + 1]
                print(f"🔗 Connecting to {conn_str}...")
                # This would parse and connect - placeholder for now
                print("SSH connection placeholder - implement connection logic")
        
        elif '--exec' in args:
            idx = args.index('--exec')
            if idx + 1 < len(args):
                command = ' '.join(args[idx + 1:])
                print(f"💻 Executing: {command}")
                # Execute on remote - placeholder
        
        elif '--disconnect' in args:
            self.ssh_manager.disconnect_all()
            print("🔌 Disconnected all SSH connections")
        
        else:
            print("SSH Commands:")
            print("  --list: List active connections")
            print("  --connect <connection>: Connect to remote")
            print("  --exec <command>: Execute command on remote")
            print("  --disconnect: Disconnect all")
    
    def handle_memory(self, args):
        """Handle memory commands"""
        if '--save' in args:
            idx = args.index('--save')
            if idx + 1 < len(args):
                key = args[idx + 1]
                value = input(f"Value for {key}> ").strip()
                self.memory.set_context(key, value)
                print(f"✅ Saved: {key} = {value}")
        
        elif '--load' in args:
            idx = args.index('--load')
            if idx + 1 < len(args):
                key = args[idx + 1]
                value = self.memory.get_context(key)
                if value:
                    print(f"📖 {key} = {value}")
                else:
                    print(f"❌ Key not found: {key}")
        
        elif '--export' in args:
            idx = args.index('--export')
            export_path = args[idx + 1] if idx + 1 < len(args) else "srcxai_memory_export.json"
            self.memory.export_memory(export_path)
            print(f"✅ Memory exported to {export_path}")
        
        elif '--search' in args:
            idx = args.index('--search')
            if idx + 1 < len(args):
                query = args[idx + 1]
                results = self.memory.search_knowledge(query)
                print(f"🔍 Search results for '{query}':")
                for result in results:
                    print(f"  - {result['title']}")
        
        else:
            print("Memory Commands:")
            print("  --save <key>: Save context")
            print("  --load <key>: Load context")
            print("  --export <path>: Export memory")
            print("  --search <query>: Search knowledge base")
    
    def handle_agent(self, args):
        """Handle agent commands"""
        if '--list' in args:
            status = self.coordinator.get_agent_status()
            print("🤖 Agent Status:")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            for name, info in status.items():
                print(f"  {name}: {info['status']}")
                if info['current_task']:
                    print(f"    Task: {info['current_task']}")
        
        elif '--status' in args:
            status = self.coordinator.get_agent_status()
            print("📊 Agent Performance:")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            for name, info in status.items():
                print(f"  {name}:")
                for k, v in info['performance'].items():
                    print(f"    {k}: {v}")
        
        elif '--start' in args:
            self.coordinator.start(num_workers=3)
            print("✅ Agent coordinator started")
        
        elif '--stop' in args:
            self.coordinator.stop()
            print("🛑 Agent coordinator stopped")
        
        else:
            print("Agent Commands:")
            print("  --list: List all agents")
            print("  --status: Show agent status")
            print("  --start: Start coordinator")
            print("  --stop: Stop coordinator")
    
    def handle_config(self, args):
        """Handle configuration commands"""
        if '--show' in args:
            print("⚙️  Current Configuration:")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"  Workspace: {self.config.workspace}")
            print(f"  Memory DB: {self.config.memory_db}")
            print(f"  Log Level: {self.config.log_level}")
            print(f"  Auto-detect AI: {self.config.auto_detect_ai}")
            print(f"  Auto-install tools: {self.config.auto_install_tools}")
            print(f"  SSH enabled: {self.config.enable_ssh}")
            print(f"  Multi-agent: {self.config.enable_multi_agent}")
            print(f"  Tab completion: {self.config.tab_completion}")
            print(f"\n  Configured Models: {len(self.config.models)}")
            print(f"  SSH Connections: {len(self.config.ssh_connections)}")
            print(f"  Agents: {len(self.config.agents)}")
        
        elif '--set' in args:
            idx = args.index('--set')
            if idx + 2 < len(args):
                key = args[idx + 1]
                value = args[idx + 2]
                
                if hasattr(self.config, key):
                    # Convert value to appropriate type
                    current_value = getattr(self.config, key)
                    if isinstance(current_value, bool):
                        value = value.lower() in ['true', 'yes', '1']
                    elif isinstance(current_value, int):
                        value = int(value)
                    
                    setattr(self.config, key, value)
                    self.config.save()
                    print(f"✅ Set {key} = {value}")
                else:
                    print(f"❌ Unknown configuration key: {key}")
        
        elif '--reset' in args:
            self.config = get_default_config()
            self.config.save()
            print("✅ Configuration reset to defaults")
        
        else:
            print("Config Commands:")
            print("  --show: Show current configuration")
            print("  --set <key> <value>: Set configuration value")
            print("  --reset: Reset to defaults")


def main():
    """Main entry point"""
    cli = SRCXAICLI()
    cli.start_interactive_mode()


if __name__ == '__main__':
    main()
