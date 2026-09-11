"""
AI System Auto-Detection Module
Automatically detects AI systems and tools on the system
"""

import os
import subprocess
import shutil
from typing import List, Dict, Optional
from pathlib import Path
import json
import re


class AIDetector:
    """Detects AI systems and tools installed on the system"""
    
    def __init__(self):
        self.detected_systems = {}
        self.common_ai_tools = {
            'ollama': {'check': self._check_ollama, 'install': self._install_ollama},
            'vllm': {'check': self._check_vllm, 'install': self._install_vllm},
            'llama.cpp': {'check': self._check_llamacpp, 'install': self._install_llamacpp},
            'openai': {'check': self._check_openai, 'install': None},
            'anthropic': {'check': self._check_anthropic, 'install': None},
            'huggingface': {'check': self._check_huggingface, 'install': self._install_huggingface},
            'langchain': {'check': self._check_langchain, 'install': self._install_langchain},
            'transformers': {'check': self._check_transformers, 'install': self._install_transformers},
        }
    
    def detect_all(self) -> Dict[str, Dict]:
        """Detect all AI systems on the system"""
        results = {}
        
        for tool_name, tool_info in self.common_ai_tools.items():
            is_installed = tool_info['check']()
            results[tool_name] = {
                'installed': is_installed,
                'version': self._get_version(tool_name) if is_installed else None,
                'install_command': tool_info['install'].__name__ if tool_info['install'] else None
            }
        
        self.detected_systems = results
        return results
    
    def _check_command(self, command: str) -> bool:
        """Check if a command is available"""
        return shutil.which(command) is not None
    
    def _check_python_package(self, package: str) -> bool:
        """Check if a Python package is installed"""
        try:
            result = subprocess.run(
                ['python3', '-c', f'import {package}'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _get_version(self, tool_name: str) -> Optional[str]:
        """Get version of a tool"""
        try:
            if tool_name == 'ollama':
                result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
                return result.stdout.strip()
            elif tool_name == 'vllm':
                result = subprocess.run(['python3', '-c', 'import vllm; print(vllm.__version__)'], 
                                      capture_output=True, text=True)
                return result.stdout.strip()
            elif tool_name in ['transformers', 'langchain']:
                package = 'transformers' if tool_name == 'transformers' else 'langchain'
                result = subprocess.run(['python3', '-c', f'import {package}; print({package}.__version__)'], 
                                      capture_output=True, text=True)
                return result.stdout.strip()
        except:
            return None
        return None
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is installed"""
        return self._check_command('ollama')
    
    def _check_vllm(self) -> bool:
        """Check if vLLM is installed"""
        return self._check_python_package('vllm')
    
    def _check_llamacpp(self) -> bool:
        """Check if llama.cpp is installed"""
        return self._check_command('llama-cli') or self._check_command('main')
    
    def _check_openai(self) -> bool:
        """Check if OpenAI API is configured"""
        api_key = os.environ.get('OPENAI_API_KEY')
        return api_key is not None and len(api_key) > 0
    
    def _check_anthropic(self) -> bool:
        """Check if Anthropic API is configured"""
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        return api_key is not None and len(api_key) > 0
    
    def _check_huggingface(self) -> bool:
        """Check if HuggingFace is configured"""
        api_key = os.environ.get('HUGGINGFACE_API_KEY') or os.environ.get('HF_TOKEN')
        return api_key is not None and len(api_key) > 0
    
    def _check_langchain(self) -> bool:
        """Check if LangChain is installed"""
        return self._check_python_package('langchain')
    
    def _check_transformers(self) -> bool:
        """Check if Transformers is installed"""
        return self._check_python_package('transformers')
    
    def _install_ollama(self) -> bool:
        """Install Ollama"""
        try:
            if shutil.which('brew'):
                subprocess.run(['brew', 'install', 'ollama'], check=True)
                return True
            else:
                # Install via curl
                subprocess.run(['curl', '-fsSL', 'https://ollama.com/install.sh', '|', 'sh'], 
                              shell=True, check=True)
                return True
        except Exception as e:
            print(f"Failed to install Ollama: {e}")
            return False
    
    def _install_vllm(self) -> bool:
        """Install vLLM"""
        try:
            subprocess.run(['pip3', 'install', 'vllm'], check=True)
            return True
        except Exception as e:
            print(f"Failed to install vLLM: {e}")
            return False
    
    def _install_llamacpp(self) -> bool:
        """Install llama.cpp"""
        try:
            # Clone and build llama.cpp
            home = Path.home()
            llama_dir = home / 'llama.cpp'
            
            if not llama_dir.exists():
                subprocess.run(['git', 'clone', 'https://github.com/ggerganov/llama.cpp'], 
                              cwd=home, check=True)
            
            subprocess.run(['make'], cwd=llama_dir, check=True)
            return True
        except Exception as e:
            print(f"Failed to install llama.cpp: {e}")
            return False
    
    def _install_huggingface(self) -> bool:
        """Install HuggingFace libraries"""
        try:
            subprocess.run(['pip3', 'install', 'huggingface_hub', 'transformers'], check=True)
            return True
        except Exception as e:
            print(f"Failed to install HuggingFace libraries: {e}")
            return False
    
    def _install_langchain(self) -> bool:
        """Install LangChain"""
        try:
            subprocess.run(['pip3', 'install', 'langchain', 'langchain-openai'], check=True)
            return True
        except Exception as e:
            print(f"Failed to install LangChain: {e}")
            return False
    
    def _install_transformers(self) -> bool:
        """Install Transformers"""
        try:
            subprocess.run(['pip3', 'install', 'transformers', 'torch'], check=True)
            return True
        except Exception as e:
            print(f"Failed to install Transformers: {e}")
            return False
    
    def auto_install_missing(self, tools: Optional[List[str]] = None) -> Dict[str, bool]:
        """Auto-install missing AI tools"""
        if tools is None:
            tools = list(self.common_ai_tools.keys())
        
        results = {}
        for tool_name in tools:
            if tool_name in self.common_ai_tools:
                tool_info = self.common_ai_tools[tool_name]
                if not tool_info['check']() and tool_info['install']:
                    print(f"Installing {tool_name}...")
                    results[tool_name] = tool_info['install']()
                else:
                    results[tool_name] = True  # Already installed or no install method
        
        return results
    
    def get_available_models(self) -> List[str]:
        """Get list of available AI models"""
        models = []
        
        # Check Ollama models
        if self._check_ollama():
            try:
                result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    models.extend([f"ollama:{line.split()[0]}" for line in lines if line.strip()])
            except:
                pass
        
        # Check for local models directory
        models_dir = Path.home() / '.cache' / 'huggingface' / 'hub'
        if models_dir.exists():
            for model_path in models_dir.iterdir():
                if model_path.is_dir():
                    models.append(f"local:{model_path.name}")
        
        return models
    
    def detect_new_systems(self, previous_detection: Dict) -> List[str]:
        """Detect newly installed AI systems since last check"""
        current_detection = self.detect_all()
        new_systems = []
        
        for system_name, current_info in current_detection.items():
            previous_info = previous_detection.get(system_name, {})
            if not previous_info.get('installed', False) and current_info['installed']:
                new_systems.append(system_name)
        
        return new_systems
