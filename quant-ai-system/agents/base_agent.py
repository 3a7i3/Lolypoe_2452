"""
Multi-Agent Trading System V7
Base class for all trading agents
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum


class AgentStatus(Enum):
    """Agent lifecycle status"""
    IDLE = 'idle'
    RUNNING = 'running'
    PROCESSING = 'processing'
    ERROR = 'error'
    STOPPED = 'stopped'


class AgentRole(Enum):
    """Agent specialized roles"""
    MARKET_SCANNER = 'market_scanner'
    STRATEGY_GENERATOR = 'strategy_generator'
    BACKTESTER = 'backtester'
    RISK_MANAGER = 'risk_manager'
    PORTFOLIO_OPTIMIZER = 'portfolio_optimizer'
    EXECUTION = 'execution'
    RESEARCH = 'research'
    COORDINATOR = 'coordinator'


@dataclass
class AgentMessage:
    """Message between agents"""
    sender_id: str
    receiver_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=low, 5=high


@dataclass
class AgentTask:
    """Task for agent to execute"""
    task_id: str
    task_type: str
    params: Dict[str, Any]
    priority: int = 1
    created_at: datetime = None


class Agent(ABC):
    """Base class for all trading agents"""
    
    def __init__(self, agent_id: str, role: AgentRole, name: str = None):
        """
        Initialize agent
        Args:
            agent_id: Unique agent identifier
            role: Agent's specialized role
            name: Human-readable name
        """
        self.agent_id = agent_id
        self.role = role
        self.name = name or f"{role.value}_{agent_id}"
        
        # Agent state
        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Logging
        self.logger = logging.getLogger(self.name)
        
        # Inbox/Outbox for message passing
        self.inbox: List[AgentMessage] = []
        self.outbox: List[AgentMessage] = []
        
        # Task queue
        self.task_queue: List[AgentTask] = []
        self.completed_tasks: List[AgentTask] = []
        
        # Performance metrics
        self.metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'total_runtime': 0
        }
        
        self.logger.info(f"✅ Agent {self.name} initialized (Role: {self.role.value})")
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method - implemented by subclasses
        Args:
            data: Input data to process
        Returns:
            Processing result
        """
        pass
    
    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task"""
        self.status = AgentStatus.RUNNING
        self.last_activity = datetime.now()
        
        try:
            self.logger.info(f"🔄 Agent {self.name} started processing...")
            result = await self.process(data)
            
            self.metrics['tasks_completed'] += 1
            self.status = AgentStatus.IDLE
            
            self.logger.info(f"✅ Agent {self.name} completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Agent {self.name} error: {str(e)}")
            self.metrics['tasks_failed'] += 1
            self.status = AgentStatus.ERROR
            return {'error': str(e), 'agent': self.name}
    
    def send_message(self, receiver_id: str, message_type: str, 
                    payload: Dict[str, Any], priority: int = 1):
        """Send message to another agent"""
        message = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now(),
            priority=priority
        )
        
        self.outbox.append(message)
        self.metrics['messages_sent'] += 1
        self.logger.debug(f"📤 Message sent to {receiver_id}: {message_type}")
    
    def receive_message(self, message: AgentMessage):
        """Receive message from another agent"""
        self.inbox.append(message)
        self.metrics['messages_received'] += 1
        self.logger.debug(f"📥 Message received from {message.sender_id}: {message.message_type}")
    
    def get_pending_messages(self, message_type: str = None) -> List[AgentMessage]:
        """Get unprocessed messages"""
        if message_type:
            return [m for m in self.inbox if m.message_type == message_type]
        return self.inbox
    
    def clear_inbox(self):
        """Clear processed messages"""
        self.inbox = []
    
    def add_task(self, task_id: str, task_type: str, params: Dict[str, Any], priority: int = 1):
        """Add task to queue"""
        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            params=params,
            priority=priority,
            created_at=datetime.now()
        )
        self.task_queue.append(task)
        self.logger.debug(f"📋 Task added: {task_id}")
    
    def get_next_task(self) -> Optional[AgentTask]:
        """Get highest priority task"""
        if not self.task_queue:
            return None
        
        # Sort by priority (higher first)
        self.task_queue.sort(key=lambda x: x.priority, reverse=True)
        return self.task_queue.pop(0)
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        uptime = (datetime.now() - self.created_at).total_seconds()
        
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'role': self.role.value,
            'status': self.status.value,
            'uptime_seconds': uptime,
            'pending_tasks': len(self.task_queue),
            'pending_messages': len(self.inbox),
            'metrics': self.metrics
        }
    
    def __repr__(self) -> str:
        return f"<Agent {self.name} ({self.role.value})>"
