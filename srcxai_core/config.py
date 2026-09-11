"""
Configuration management for SRCXAI
"""

import os
import json
import pathlib
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class AIModelConfig:
    """Configuration for AI models"""
    name: str
    provider: str
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model_type: str = "chat"  # chat, completion, embedding
    capabilities: list = field(default_factory=list)
    installed: bool = False
    auto_detected: bool = False


@dataclass
class SSHConfig:
    """Configuration for SSH connections"""
    host: str
    username: str
    port: int = 22
    key_path: Optional[str] = None
    password: Optional[str] = None
    alias: Optional[str] = None


@dataclass
class AgentConfig:
    """Configuration for individual agents"""
    name: str
    role: str
    model: str
    capabilities: list = field(default_factory=list)
    enabled: bool = True


@dataclass
class SRCXAIConfig:
    """Main configuration for SRCXAI"""
    workspace: str = field(default_factory=lambda: str(pathlib.Path.home() / "srcxai_workspace"))
    memory_db: str = field(default_factory=lambda: str(pathlib.Path.home() / "srcxai_memory.db"))
    log_level: str = "INFO"
    auto_detect_ai: bool = True
    auto_install_tools: bool = True
    enable_ssh: bool = True
    enable_multi_agent: bool = True
    tab_completion: bool = True
    models: Dict[str, AIModelConfig] = field(default_factory=dict)
    ssh_connections: Dict[str, SSHConfig] = field(default_factory=dict)
    agents: Dict[str, AgentConfig] = field(default_factory=dict)
    
    def save(self, path: Optional[str] = None):
        """Save configuration to file"""
        if path is None:
            path = os.path.join(self.workspace, "config.json")
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        config_dict = asdict(self)
        # Convert dataclass instances to dicts for JSON serialization
        config_dict['models'] = {k: asdict(v) for k, v in self.models.items()}
        config_dict['ssh_connections'] = {k: asdict(v) for k, v in self.ssh_connections.items()}
        config_dict['agents'] = {k: asdict(v) for k, v in self.agents.items()}
        
        with open(path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def load(cls, path: Optional[str] = None) -> 'SRCXAIConfig':
        """Load configuration from file"""
        if path is None:
            path = os.path.join(str(pathlib.Path.home()), "srcxai_workspace", "config.json")
        
        if not os.path.exists(path):
            return cls()
        
        with open(path, 'r') as f:
            config_dict = json.load(f)
        
        # Reconstruct dataclass instances
        models = {k: AIModelConfig(**v) for k, v in config_dict.get('models', {}).items()}
        ssh_connections = {k: SSHConfig(**v) for k, v in config_dict.get('ssh_connections', {}).items()}
        agents = {k: AgentConfig(**v) for k, v in config_dict.get('agents', {}).items()}
        
        config_dict['models'] = models
        config_dict['ssh_connections'] = ssh_connections
        config_dict['agents'] = agents
        
        return cls(**config_dict)


def get_default_config() -> SRCXAIConfig:
    """Get default configuration with common AI models"""
    config = SRCXAIConfig()
    
    # Add common AI models
    config.models['gpt-4'] = AIModelConfig(
        name="gpt-4",
        provider="openai",
        capabilities=["chat", "code", "analysis"],
        installed=False
    )
    config.models['claude-3'] = AIModelConfig(
        name="claude-3",
        provider="anthropic",
        capabilities=["chat", "code", "analysis"],
        installed=False
    )
    config.models['local-llama'] = AIModelConfig(
        name="local-llama",
        provider="local",
        capabilities=["chat", "code"],
        installed=False
    )
    
    # Add default agents
    config.agents['coder'] = AgentConfig(
        name="coder",
        role="code_generation",
        model="gpt-4",
        capabilities=["write_code", "debug", "refactor"]
    )
    config.agents['analyst'] = AgentConfig(
        name="analyst",
        role="analysis",
        model="claude-3",
        capabilities=["analyze", "summarize", "research"]
    )
    config.agents['executor'] = AgentConfig(
        name="executor",
        role="execution",
        model="local-llama",
        capabilities=["run_commands", "file_operations"]
    )
    
    return config
