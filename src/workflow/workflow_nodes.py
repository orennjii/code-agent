"""
工作流节点定义
"""

from typing import Dict, Any, Optional
from langchain_core.language_models import BaseLanguageModel

from ..agents import (
    PlannerAgent, CoderAgent, TesterAgent, 
    DebuggerAgent, DocumenterAgent
)
from .workflow_state import WorkflowState, WorkflowStatus


class WorkflowNodes:
    """工作流节点类"""
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.planner = PlannerAgent(llm)
        self.coder = CoderAgent(llm)
        self.tester = TesterAgent(llm)
        self.debugger = DebuggerAgent(llm)
        self.documenter = DocumenterAgent(llm)
    
    async def planning_node(self, state: WorkflowState) -> Dict[str, Any]:
        """规划节点"""
        print(f"🔄 开始规划阶段: {state.user_request}")
        
        state.update_status(WorkflowStatus.PLANNING)
        state.current_task = "规划开发任务"
        
        try:
            # 执行规划
            plan_result = await self.planner.execute(state.user_request)
            state.planner_result = plan_result
            state.set_context("plan", plan_result)
            
            state.add_completed_task("规划")
            print(f"✅ 规划完成")
            
            return {"state": state}
            
        except Exception as e:
            error_msg = f"规划失败: {str(e)}"
            state.add_error(error_msg)
            state.add_failed_task("规划")
            print(f"❌ {error_msg}")
            return {"state": state}
    
    async def coding_node(self, state: WorkflowState) -> Dict[str, Any]:
        """编码节点"""
        print(f"🔄 开始编码阶段")
        
        state.update_status(WorkflowStatus.CODING)
        state.current_task = "生成代码"
        
        try:
            # 准备上下文
            context = {
                "plan": state.planner_result,
                "iteration": state.iteration_count
            }
            
            # 执行编码
            code_result = await self.coder.execute(state.user_request, context)
            state.coder_result = code_result
            state.set_context("generated_code", code_result)
            
            state.add_completed_task("编码")
            print(f"✅ 编码完成")
            
            return {"state": state}
            
        except Exception as e:
            error_msg = f"编码失败: {str(e)}"
            state.add_error(error_msg)
            state.add_failed_task("编码")
            print(f"❌ {error_msg}")
            return {"state": state}
    
    async def testing_node(self, state: WorkflowState) -> Dict[str, Any]:
        """测试节点"""
        print(f"🔄 开始测试阶段")
        
        state.update_status(WorkflowStatus.TESTING)
        state.current_task = "执行测试"
        
        try:
            # 准备上下文
            context = {
                "generated_code": state.coder_result or state.get_context("generated_code"),
                "plan": state.planner_result
            }
            
            # 执行测试
            test_result = await self.tester.execute(state.user_request, context)
            state.tester_result = test_result
            state.set_context("test_result", test_result)
            
            state.add_completed_task("测试")
            
            if test_result.get("status") == "passed":
                print(f"✅ 测试通过")
            else:
                print(f"⚠️ 测试失败，需要调试")
            
            return {"state": state}
            
        except Exception as e:
            error_msg = f"测试失败: {str(e)}"
            state.add_error(error_msg)
            state.add_failed_task("测试")
            print(f"❌ {error_msg}")
            return {"state": state}
    
    async def debugging_node(self, state: WorkflowState) -> Dict[str, Any]:
        """调试节点"""
        print(f"🔄 开始调试阶段")
        
        state.update_status(WorkflowStatus.DEBUGGING)
        state.current_task = "调试和修复代码"
        
        try:
            # 准备上下文
            context = {
                "generated_code": state.coder_result or state.get_context("generated_code"),
                "test_result": state.tester_result,
                "plan": state.planner_result
            }
            
            # 执行调试
            debug_result = await self.debugger.execute(state.user_request, context)
            state.debugger_result = debug_result
            state.set_context("debug_result", debug_result)
            
            # 更新代码结果
            if debug_result.get("fixed_code"):
                state.coder_result = {
                    "code": debug_result["fixed_code"],
                    "status": "fixed",
                    "iteration": state.iteration_count
                }
                state.set_context("generated_code", state.coder_result)
            
            state.add_completed_task("调试")
            state.increment_iteration()
            
            print(f"✅ 调试完成 (迭代 {state.iteration_count})")
            
            return {"state": state}
            
        except Exception as e:
            error_msg = f"调试失败: {str(e)}"
            state.add_error(error_msg)
            state.add_failed_task("调试")
            print(f"❌ {error_msg}")
            return {"state": state}
    
    async def documenting_node(self, state: WorkflowState) -> Dict[str, Any]:
        """文档生成节点"""
        print(f"🔄 开始文档生成阶段")
        
        state.update_status(WorkflowStatus.DOCUMENTING)
        state.current_task = "生成文档"
        
        try:
            # 准备上下文
            context = {
                "generated_code": state.coder_result or state.get_context("generated_code"),
                "test_result": state.tester_result,
                "debug_result": state.debugger_result,
                "plan": state.planner_result
            }
            
            # 执行文档生成
            doc_result = await self.documenter.execute(state.user_request, context)
            state.documenter_result = doc_result
            state.set_context("documentation", doc_result)
            
            # 设置最终结果
            state.final_code = state.get_latest_code()
            state.final_documentation = doc_result.get("readme", "")
            
            state.add_completed_task("文档生成")
            state.update_status(WorkflowStatus.COMPLETED)
            
            print(f"✅ 文档生成完成")
            print(f"🎉 工作流完成!")
            
            return {"state": state}
            
        except Exception as e:
            error_msg = f"文档生成失败: {str(e)}"
            state.add_error(error_msg)
            state.add_failed_task("文档生成")
            print(f"❌ {error_msg}")
            return {"state": state}
    
    def should_debug(self, state: WorkflowState) -> bool:
        """判断是否需要调试"""
        return state.needs_debugging()
    
    def should_continue_iteration(self, state: WorkflowState) -> bool:
        """判断是否继续迭代"""
        return (
            state.needs_debugging() and 
            state.can_continue_iteration()
        )
    
    def should_generate_documentation(self, state: WorkflowState) -> bool:
        """判断是否应该生成文档"""
        return (
            state.tester_result is not None and
            state.tester_result.get("status") == "passed"
        )
    
    def get_next_node(self, state: WorkflowState) -> Optional[str]:
        """获取下一个节点"""
        if state.status == WorkflowStatus.PENDING:
            return "planning"
        elif state.status == WorkflowStatus.PLANNING:
            return "coding"
        elif state.status == WorkflowStatus.CODING:
            return "testing"
        elif state.status == WorkflowStatus.TESTING:
            if self.should_debug(state):
                return "debugging"
            elif self.should_generate_documentation(state):
                return "documenting"
            else:
                return "documenting"  # 即使测试失败，也生成文档
        elif state.status == WorkflowStatus.DEBUGGING:
            if self.should_continue_iteration(state):
                return "testing"  # 重新测试
            else:
                return "documenting"  # 超过最大迭代次数，生成文档
        elif state.status == WorkflowStatus.DOCUMENTING:
            return None  # 工作流结束
        else:
            return None
