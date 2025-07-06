"""
工作流状态管理
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    PLANNING = "planning"
    CODING = "coding"
    TESTING = "testing"
    DEBUGGING = "debugging"
    DOCUMENTING = "documenting"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowState(BaseModel):
    """工作流状态类"""
    
    # 基本信息
    workflow_id: str = Field(description="工作流ID")
    user_request: str = Field(description="用户请求")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING, description="工作流状态")
    
    # 任务信息
    current_task: Optional[str] = Field(default=None, description="当前任务")
    completed_tasks: List[str] = Field(default_factory=list, description="已完成任务")
    failed_tasks: List[str] = Field(default_factory=list, description="失败任务")
    
    # 智能体结果
    planner_result: Optional[Dict[str, Any]] = Field(default=None, description="规划师结果")
    coder_result: Optional[Dict[str, Any]] = Field(default=None, description="程序员结果")
    tester_result: Optional[Dict[str, Any]] = Field(default=None, description="测试员结果")
    debugger_result: Optional[Dict[str, Any]] = Field(default=None, description="调试器结果")
    documenter_result: Optional[Dict[str, Any]] = Field(default=None, description="文档工程师结果")
    
    # 迭代信息
    iteration_count: int = Field(default=0, description="迭代次数")
    max_iterations: int = Field(default=3, description="最大迭代次数")
    
    # 错误信息
    last_error: Optional[str] = Field(default=None, description="最后错误信息")
    error_history: List[str] = Field(default_factory=list, description="错误历史")
    
    # 上下文信息
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文数据")
    
    # 输出信息
    final_code: Optional[str] = Field(default=None, description="最终代码")
    final_documentation: Optional[str] = Field(default=None, description="最终文档")
    
    def update_status(self, new_status: WorkflowStatus) -> None:
        """更新工作流状态"""
        self.status = new_status
    
    def add_completed_task(self, task: str) -> None:
        """添加已完成任务"""
        if task not in self.completed_tasks:
            self.completed_tasks.append(task)
    
    def add_failed_task(self, task: str) -> None:
        """添加失败任务"""
        if task not in self.failed_tasks:
            self.failed_tasks.append(task)
    
    def add_error(self, error: str) -> None:
        """添加错误信息"""
        self.last_error = error
        self.error_history.append(error)
    
    def increment_iteration(self) -> None:
        """增加迭代次数"""
        self.iteration_count += 1
    
    def can_continue_iteration(self) -> bool:
        """是否可以继续迭代"""
        return self.iteration_count < self.max_iterations
    
    def set_context(self, key: str, value: Any) -> None:
        """设置上下文数据"""
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.context.get(key, default)
    
    def get_latest_code(self) -> Optional[str]:
        """获取最新代码"""
        # 优先返回调试器修复的代码
        if self.debugger_result and self.debugger_result.get("fixed_code"):
            return self.debugger_result["fixed_code"]
        
        # 其次返回程序员生成的代码
        if self.coder_result and self.coder_result.get("code"):
            return self.coder_result["code"]
        
        return None
    
    def get_test_status(self) -> str:
        """获取测试状态"""
        if self.tester_result:
            return self.tester_result.get("status", "unknown")
        return "not_tested"
    
    def needs_debugging(self) -> bool:
        """是否需要调试"""
        return (
            self.tester_result is not None and 
            self.tester_result.get("status") == "failed" and
            self.can_continue_iteration()
        )
    
    def is_workflow_complete(self) -> bool:
        """工作流是否完成"""
        return (
            self.status == WorkflowStatus.COMPLETED or
            self.status == WorkflowStatus.FAILED or
            not self.can_continue_iteration()
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """获取工作流摘要"""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "iteration_count": self.iteration_count,
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "has_code": self.get_latest_code() is not None,
            "test_status": self.get_test_status(),
            "has_documentation": self.documenter_result is not None,
            "last_error": self.last_error
        }
