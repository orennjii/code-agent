"""
LangGraph工作流图定义
"""

from typing import Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END
from langchain_core.language_models import BaseLanguageModel

from .workflow_state import WorkflowState, WorkflowStatus
from .workflow_nodes import WorkflowNodes


class WorkflowGraph:
    """工作流图类"""
    
    def __init__(self, llm: BaseLanguageModel, max_iterations: int = 3):
        self.llm = llm
        self.max_iterations = max_iterations
        self.nodes = WorkflowNodes(llm)
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """构建工作流图"""
        # 创建状态图
        workflow = StateGraph(WorkflowState)
        
        # 添加节点
        workflow.add_node("planning", self._planning_wrapper)
        workflow.add_node("coding", self._coding_wrapper)
        workflow.add_node("testing", self._testing_wrapper)
        workflow.add_node("debugging", self._debugging_wrapper)
        workflow.add_node("documenting", self._documenting_wrapper)
        
        # 设置入口点
        workflow.set_entry_point("planning")
        
        # 添加边
        workflow.add_edge("planning", "coding")
        workflow.add_edge("coding", "testing")
        
        # 条件边：测试后的路径选择
        workflow.add_conditional_edges(
            "testing",
            self._route_after_testing,
            {
                "debugging": "debugging",
                "documenting": "documenting",
                "end": END
            }
        )
        
        # 条件边：调试后的路径选择
        workflow.add_conditional_edges(
            "debugging",
            self._route_after_debugging,
            {
                "testing": "testing",
                "documenting": "documenting",
                "end": END
            }
        )
        
        # 文档生成后结束
        workflow.add_edge("documenting", END)
        
        # 编译图
        return workflow.compile()
    
    async def _planning_wrapper(self, state: WorkflowState) -> WorkflowState:
        """规划节点包装器"""
        result = await self.nodes.planning_node(state)
        return result["state"]
    
    async def _coding_wrapper(self, state: WorkflowState) -> WorkflowState:
        """编码节点包装器"""
        result = await self.nodes.coding_node(state)
        return result["state"]
    
    async def _testing_wrapper(self, state: WorkflowState) -> WorkflowState:
        """测试节点包装器"""
        result = await self.nodes.testing_node(state)
        return result["state"]
    
    async def _debugging_wrapper(self, state: WorkflowState) -> WorkflowState:
        """调试节点包装器"""
        result = await self.nodes.debugging_node(state)
        return result["state"]
    
    async def _documenting_wrapper(self, state: WorkflowState) -> WorkflowState:
        """文档生成节点包装器"""
        result = await self.nodes.documenting_node(state)
        return result["state"]
    
    def _route_after_testing(self, state: WorkflowState) -> Literal["debugging", "documenting", "end"]:
        """测试后的路由决策"""
        if state.status == WorkflowStatus.FAILED:
            return "end"
        
        # 检查是否达到最大迭代次数
        if not state.can_continue_iteration():
            print(f"⏹️ 达到最大迭代次数({state.max_iterations})，停止调试")
            return "documenting"
        
        # 如果测试失败且可以继续迭代，进行调试
        if self.nodes.should_debug(state):
            return "debugging"
        
        # 如果测试通过或无法继续调试，生成文档
        if self.nodes.should_generate_documentation(state):
            return "documenting"
        
        return "end"
    
    def _route_after_debugging(self, state: WorkflowState) -> Literal["testing", "documenting", "end"]:
        """调试后的路由决策"""
        if state.status == WorkflowStatus.FAILED:
            return "end"
        
        # 检查是否达到最大迭代次数
        if not state.can_continue_iteration():
            print(f"⏹️ 达到最大迭代次数({state.max_iterations})，停止调试")
            return "documenting"
        
        # 如果可以继续迭代，重新测试
        if self.nodes.should_continue_iteration(state):
            return "testing"
        
        # 否则生成文档
        return "documenting"
    
    async def execute(self, user_request: str, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """执行工作流"""
        if not workflow_id:
            import uuid
            workflow_id = str(uuid.uuid4())
        
        # 初始化状态
        initial_state = WorkflowState(
            workflow_id=workflow_id,
            user_request=user_request,
            status=WorkflowStatus.PENDING,
            max_iterations=self.max_iterations
        )
        
        print(f"🚀 开始执行工作流: {workflow_id}")
        print(f"📋 用户请求: {user_request}")
        
        try:
            # 执行工作流
            result = await self.graph.ainvoke(initial_state)
            
            # LangGraph返回的是最终状态对象
            if isinstance(result, WorkflowState):
                final_state = result
            else:
                # 如果返回的是字典，需要重构为WorkflowState
                final_state = WorkflowState(**result)
            
            print(f"📊 工作流执行完成")
            print(f"状态: {final_state.status.value}")
            print(f"迭代次数: {final_state.iteration_count}")
            print(f"已完成任务: {len(final_state.completed_tasks)}")
            print(f"失败任务: {len(final_state.failed_tasks)}")
            
            return {
                "success": final_state.status == WorkflowStatus.COMPLETED,
                "workflow_id": final_state.workflow_id,
                "status": final_state.status.value,
                "final_code": final_state.final_code,
                "final_documentation": final_state.final_documentation,
                "summary": final_state.get_summary(),
                "iteration_count": final_state.iteration_count,
                "completed_tasks": final_state.completed_tasks,
                "failed_tasks": final_state.failed_tasks,
                "error_history": final_state.error_history
            }
                
        except Exception as e:
            error_msg = f"工作流执行异常: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "workflow_id": workflow_id,
                "status": "failed",
                "final_code": None,
                "final_documentation": None,
                "summary": {},
                "iteration_count": 0,
                "completed_tasks": [],
                "failed_tasks": [],
                "error_history": [error_msg]
            }
    
    def get_graph_structure(self) -> Dict[str, Any]:
        """获取图结构信息"""
        return {
            "nodes": ["planning", "coding", "testing", "debugging", "documenting"],
            "edges": [
                ("planning", "coding"),
                ("coding", "testing"),
                ("testing", "debugging"),
                ("testing", "documenting"),
                ("debugging", "testing"),
                ("debugging", "documenting"),
                ("documenting", "END")
            ],
            "conditional_edges": [
                ("testing", ["debugging", "documenting", "end"]),
                ("debugging", ["testing", "documenting", "end"])
            ],
            "entry_point": "planning",
            "description": "LangGraph驱动的多智能体协作工作流"
        }
    
    def visualize(self) -> None:
        """可视化工作流图"""
        try:
            # 尝试打印图结构
            print("工作流图结构:")
            structure = self.get_graph_structure()
            print(f"节点: {structure['nodes']}")
            print(f"边: {structure['edges']}")
            print(f"条件边: {structure['conditional_edges']}")
            print(f"入口点: {structure['entry_point']}")
        except Exception as e:
            print(f"可视化失败: {e}")
    
    def get_execution_history(self) -> Dict[str, Any]:
        """获取执行历史（如果支持）"""
        # 这里可以添加执行历史追踪逻辑
        return {
            "message": "执行历史功能待实现",
            "supported": False
        }
