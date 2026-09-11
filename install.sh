#!/bin/bash

# SRCXAI Installation Script for macOS

set -e

echo "🚀 Installing SRCXAI Multi-Agent System..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Python version
echo "🐍 Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "✅ Python $PYTHON_VERSION found"
else
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is available
echo "📦 Checking pip..."
if command -v pip3 &> /dev/null; then
    echo "✅ pip3 found"
else
    echo "❌ pip3 not found. Installing..."
    python3 -m ensurepip --upgrade
fi

# Create virtual environment (optional but recommended)
echo "🔧 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Install SRCXAI in development mode
echo "🔨 Installing SRCXAI..."
pip install -e .

# Create workspace directory
echo "📁 Creating workspace directory..."
mkdir -p ~/srcxai_workspace

# Create initial configuration
echo "⚙️  Setting up configuration..."
python3 -c "from srcxai_core.config import get_default_config; config = get_default_config(); config.save()"

# Setup auto-completion
echo "🔧 Setting up shell auto-completion..."
SHELL_RC=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "srcxai" "$SHELL_RC"; then
        echo "" >> "$SHELL_RC"
        echo "# SRCXAI auto-completion" >> "$SHELL_RC"
        echo "eval \"\$(register-python-argcomplete srcxai)\" 2>/dev/null || true" >> "$SHELL_RC"
        echo "✅ Auto-completion added to $SHELL_RC"
    else
        echo "ℹ️  Auto-completion already configured"
    fi
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SRCXAI installation complete!"
echo  ""
echo "📖 Quick Start:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run SRCXAI: srcxai"
echo "  3. Type 'help' for available commands"
echo ""
echo "🔧 Optional: Install local AI tools"
echo "  - Ollama: brew install ollama"
echo "  - vLLM: pip install vllm"
echo ""
echo "📚 Documentation: https://github.com/srcxai/srcxai"
