"""
Multi-Agent Coordination System
Manages multiple AI agents and coordinates their activities
"""

import asyncio
import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import threading
import queue


class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class AgentTask:
    """Task for an agent"""
    id: str
    description: str
    agent_type: str
    priority: int = 0
    parameters: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    result: Optional[Any] = None
    status: AgentStatus = AgentStatus.IDLE


@dataclass
class Agent:
    """AI Agent representation"""
    name: str
    role: str
    model: str
    capabilities: List[str]
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[AgentTask] = None
    performance_metrics: Dict = field(default_factory=dict)


class MultiAgentCoordinator:
    """Coordinates multiple AI agents"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.task_queue: queue.Queue = queue.Queue()
        self.task_results: Dict[str, Any] = {}
        self.running = False
        self.worker_threads: List[threading.Thread] = []
        self.lock = threading.Lock()
    
    def register_agent(self, name: str, role: str, model: str, 
                      capabilities: List[str]) -> Agent:
        """Register a new agent"""
        agent = Agent(
            name=name,
            role=role,
            model=model,
            capabilities=capabilities
        )
        
        with self.lock:
            self.agents[name] = agent
        
        return agent
    
    def unregister_agent(self, name: str):
        """Unregister an agent"""
        with self.lock:
            if name in self.agents:
                del self.agents[name]
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get agent by name"""
        return self.agents.get(name)
    
    def get_available_agents(self, capability: Optional[str] = None) -> List[Agent]:
        """Get available agents, optionally filtered by capability"""
        available = []
        
        with self.lock:
            for agent in self.agents.values():
                if agent.status == AgentStatus.IDLE:
                    if capability is None or capability in agent.capabilities:
                        available.append(agent)
        
        return available
    
    def submit_task(self, task: AgentTask) -> str:
        """Submit a task to the coordinator"""
        self.task_queue.put(task)
        return task.id
    
    def submit_simple_task(self, description: str, agent_type: str, 
                          parameters: Optional[Dict] = None) -> str:
        """Submit a simple task"""
        import uuid
        task = AgentTask(
            id=str(uuid.uuid4()),
            description=description,
            agent_type=agent_type,
            parameters=parameters or {}
        )
        return self.submit_task(task)
    
    def start(self, num_workers: int = 3):
        """Start the coordinator with worker threads"""
        self.running = True
        
        for i in range(num_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.worker_threads.append(worker)
    
    def stop(self):
        """Stop the coordinator"""
        self.running = False
        
        # Wait for workers to finish
        for worker in self.worker_threads:
            worker.join(timeout=5)
        
        self.worker_threads.clear()
    
    def _worker_loop(self):
        """Worker thread loop"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                self._process_task(task)
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker error: {e}")
    
    def _process_task(self, task: AgentTask):
        """Process a task"""
        # Find suitable agent
        agent = self._find_suitable_agent(task)
        
        if not agent:
            print(f"No available agent for task: {task.description}")
            task.status = AgentStatus.ERROR
            return
        
        # Assign task to agent
        with self.lock:
            agent.status = AgentStatus.WORKING
            agent.current_task = task
            task.status = AgentStatus.WORKING
        
        try:
            # Execute task (this would be implemented by specific agent handlers)
            result = self._execute_task(agent, task)
            
            with self.lock:
                task.result = result
                task.status = AgentStatus.IDLE
                agent.status = AgentStatus.IDLE
                agent.current_task = None
                self.task_results[task.id] = result
            
        except Exception as e:
            print(f"Task execution error: {e}")
            with self.lock:
                task.status = AgentStatus.ERROR
                agent.status = AgentStatus.ERROR
                agent.current_task = None
    
    def _find_suitable_agent(self, task: AgentTask) -> Optional[Agent]:
        """Find a suitable agent for a task"""
        available_agents = self.get_available_agents(task.agent_type)
        
        if not available_agents:
            return None
        
        # Select agent with best performance for this task type
        return available_agents[0]
    
    def _execute_task(self, agent: Agent, task: AgentTask) -> Any:
        """Execute task using agent (to be implemented by specific agent types)"""
        # This is a placeholder - actual implementation would depend on agent type
        print(f"Agent {agent.name} executing task: {task.description}")
        
        # Simulate task execution
        import time
        time.sleep(1)
        
        return f"Task completed by {agent.name}"
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get result of a task"""
        return self.task_results.get(task_id)
    
    def get_agent_status(self) -> Dict[str, Dict]:
        """Get status of all agents"""
        with self.lock:
            return {
                name: {
                    'status': agent.status.value,
                    'current_task': agent.current_task.description if agent.current_task else None,
                    'performance': agent.performance_metrics
                }
                for name, agent in self.agents.items()
            }
    
    def coordinate_collaborative_task(self, task_description: str, 
                                      required_roles: List[str]) -> Dict[str, Any]:
        """Coordinate a collaborative task requiring multiple agents"""
        results = {}
        
        for role in required_roles:
            agents = self.get_available_agents(role)
            if agents:
                task = AgentTask(
                    id=f"collab_{role}",
                    description=f"{task_description} ({role})",
                    agent_type=role
                )
                task_id = self.submit_task(task)
                results[role] = task_id
            else:
                results[role] = None
        
        return results


class CoderAgent:
    """Specialized agent for code generation and editing"""
    
    def __init__(self, model: str, memory_manager):
        self.model = model
        self.memory = memory_manager
        self.capabilities = ["write_code", "debug", "refactor", "explain_code"]
    
    def write_code(self, description: str, language: str, context: Optional[Dict] = None) -> str:
        """Generate code based on description"""
        # This would integrate with actual AI model
        code = f"# Generated code for: {description}\n# Language: {language}\n"
        
        # Log to memory
        self.memory.add_conversation_message(
            session_id="coder",
            role="assistant",
            content=code,
            metadata={"task": "write_code", "language": language}
        )
        
        return code
    
    def debug_code(self, code: str, error: str) -> str:
        """Debug code and provide fixes"""
        # This would integrate with actual AI model
        analysis = f"Debug analysis for error: {error}\n"
        
        self.memory.add_conversation_message(
            session_id="coder",
            role="assistant",
            content=analysis,
            metadata={"task": "debug", "error": error}
        )
        
        return analysis


class AnalystAgent:
    """Specialized agent for analysis and research"""
    
    def __init__(self, model: str, memory_manager):
        self.model = model
        self.memory = memory_manager
        self.capabilities = ["analyze", "summarize", "research", "compare"]
    
    def analyze(self, data: Any, analysis_type: str) -> str:
        """Analyze data and provide insights"""
        # This would integrate with actual AI model
        analysis = f"Analysis of type: {analysis_type}\n"
        
        self.memory.add_conversation_message(
            session_id="analyst",
            role="assistant",
            content=analysis,
            metadata={"task": "analyze", "type": analysis_type}
        )
        
        return analysis
    
    def summarize(self, text: str, max_length: int = 200) -> str:
        """Summarize text"""
        # This would integrate with actual AI model
        summary = text[:max_length] + "..." if len(text) > max_length else text
        
        self.memory.add_conversation_message(
            session_id="analyst",
            role="assistant",
            content=summary,
            metadata={"task": "summarize", "original_length": len(text)}
        )
        
        return summary


class ExecutorAgent:
    """Specialized agent for executing commands and file operations"""
    
    def __init__(self, model: str, memory_manager):
        self.model = model
        self.memory = memory_manager
        self.capabilities = ["run_commands", "file_operations", "system_admin"]
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a system command"""
        import subprocess
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
            self.memory.add_conversation_message(
                session_id="executor",
                role="assistant",
                content=f"Executed: {command}",
                metadata={"task": "execute_command", "result": output}
            )
            
            return output
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
