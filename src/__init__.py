"""
多智能体协作系统
基于LangChain和LangGraph的自动化软件开发工作流
"""

from .main import MultiAgentWorkflow
from .config import Config
from .workflow import WorkflowGraph, WorkflowState, WorkflowNodes
from .agents import (
    BaseAgent, PlannerAgent, CoderAgent, 
    TesterAgent, DebuggerAgent, DocumenterAgent
)
from .tools import FileTools, CodeExecutionTools, AnalysisTools

__version__ = "1.0.0"
__author__ = "Multi-Agent Team"
__description__ = "基于LangChain和LangGraph的多智能体协作系统"

__all__ = [
    "MultiAgentWorkflow",
    "Config",
    "WorkflowGraph",
    "WorkflowState", 
    "WorkflowNodes",
    "BaseAgent",
    "PlannerAgent",
    "CoderAgent",
    "TesterAgent",
    "DebuggerAgent",
    "DocumenterAgent",
    "FileTools",
    "CodeExecutionTools",
    "AnalysisTools"
]