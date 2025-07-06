"""
基础智能体类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """智能体状态"""
    messages: List[BaseMessage] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    current_task: Optional[str] = None
    status: str = "idle"  # idle, working, completed, error
    result: Optional[Any] = None
    error: Optional[str] = None


class BaseAgent(ABC):
    """基础智能体类"""
    
    def __init__(
        self,
        name: str,
        llm: BaseLanguageModel,
        description: str = "",
        system_prompt: str = "",
        tools: Optional[List[Any]] = None
    ):
        self.name = name
        self.llm = llm
        self.description = description
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.state = AgentState()
    
    @abstractmethod
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """执行智能体任务"""
        pass
    
    def update_state(self, **kwargs) -> None:
        """更新智能体状态"""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
    
    def add_message(self, message: BaseMessage) -> None:
        """添加消息到状态"""
        self.state.messages.append(message)
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文信息"""
        return self.state.context.get(key, default)
    
    def set_context(self, key: str, value: Any) -> None:
        """设置上下文信息"""
        self.state.context[key] = value
    
    def reset_state(self) -> None:
        """重置智能体状态"""
        self.state = AgentState()
    
    def __str__(self) -> str:
        return f"{self.name} - {self.description}"
