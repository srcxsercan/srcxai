# SRCXAI Multi-Agent System v2.0

Advanced AI system with auto-detection, SSH capabilities, persistent memory, and multi-agent coordination.

## Features

- **🤖 Multi-Agent Architecture**: Coordinate multiple specialized AI agents (Coder, Analyst, Executor)
- **🔍 Auto-Detection**: Automatically detect AI systems and tools on your macOS system
- **📦 Auto-Installation**: Automatically install missing AI tools and dependencies
- **🔗 SSH Remote Editing**: Connect to remote systems via SSH and edit files remotely
- **🧠 Persistent Memory**: Long-term memory with conversation history and context management
- **⌨️ Tab Completion**: Intelligent tab completion for commands, files, and AI models
- **🛡️ Error Handling**: Robust error handling with circuit breakers and retry mechanisms
- **⚙️ Configuration Management**: Comprehensive configuration system with persistence

## Quick Start

### Installation

```bash
# Clone or navigate to srcxai directory
cd /Users/macbookpro/srcxai

# Run installation script
chmod +x install.sh
./install.sh

# Or install manually
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Start SRCXAI
srcxai
```

## Commands

- `help` - Show available commands
- `detect` - Detect AI systems on the system
- `install` - Install AI tools and models
- `chat` - Start chat with AI model
- `code` - Generate or edit code
- `ssh` - SSH to remote system
- `memory` - Manage memory and context
- `agent` - Manage multi-agent system
- `config` - Manage configuration
- `exit` - Exit SRCXAI

## Supported AI Systems

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude-3)
- Local models via Ollama
- vLLM for local inference
- HuggingFace Transformers
- LangChain integration

## SSH Capabilities

- Connect to remote systems
- Execute commands remotely
- Edit files remotely
- Upload/download files
- Directory synchronization
- Multiple connection management

## Memory System

- Conversation history
- Context storage
- Task tracking
- Knowledge base
- File operation logging
- Export/import functionality

## Configuration

Configuration is stored in `~/srcxai_workspace/config.json`. Key settings:

- `auto_detect_ai`: Enable automatic AI system detection
- `auto_install_tools`: Enable automatic tool installation
- `enable_ssh`: Enable SSH capabilities
- `enable_multi_agent`: Enable multi-agent coordination
- `tab_completion`: Enable tab completion

## Architecture

```
srcxai/
├── srcxai_core/
│   ├── __init__.py       # Package initialization
│   ├── config.py         # Configuration management
│   ├── ai_detector.py    # AI system auto-detection
│   ├── memory.py         # Persistent memory system
│   ├── ssh_manager.py    # SSH remote editing
│   ├── multi_agent.py    # Multi-agent coordination
│   ├── tab_completion.py # Tab completion system
│   ├── error_handler.py  # Error handling & stability
│   └── cli.py           # Main CLI interface
├── requirements.txt      # Python dependencies
├── setup.py            # Package setup
└── install.sh          # Installation script
```

## Requirements

- Python 3.8+
- macOS (optimized for macOS)
- Internet connection (for AI APIs and tool installation)

## License

MIT License
