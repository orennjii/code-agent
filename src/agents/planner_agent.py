"""
规划师智能体 - 负责分析需求并制定开发计划
"""

from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models import BaseLanguageModel
from .base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """规划师智能体"""
    
    def __init__(self, llm: BaseLanguageModel):
        system_prompt = """你是一个专业的软件开发规划师。你的任务是：
1. 分析用户的功能需求
2. 将复杂需求分解为可执行的子任务
3. 制定详细的开发计划
4. 确定每个子任务的优先级和依赖关系

请用清晰、结构化的方式回复，包含：
- 需求分析
- 任务分解
- 实现步骤
- 预期结果
"""
        super().__init__(
            name="规划师",
            llm=llm,
            description="分析需求并制定开发计划",
            system_prompt=system_prompt
        )
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行规划任务"""
        self.update_state(status="working", current_task=task)
        
        try:
            # 构建规划提示
            planning_prompt = f"""
{self.system_prompt}

用户需求：{task}

请分析这个需求并制定详细的开发计划。
"""
            
            # 添加用户消息
            self.add_message(HumanMessage(content=planning_prompt))
            
            # 调用LLM生成计划
            response = await self.llm.ainvoke(self.state.messages)
            self.add_message(response)
            
            # 解析计划
            plan = self._parse_plan(response.content)
            
            self.update_state(status="completed", result=plan)
            self.set_context("plan", plan)
            
            return plan
            
        except Exception as e:
            self.update_state(status="error", error=str(e))
            raise
    
    def _parse_plan(self, plan_text: str) -> Dict[str, Any]:
        """解析规划文本为结构化数据"""
        return {
            "raw_plan": plan_text,
            "tasks": self._extract_tasks(plan_text),
            "priority": "high",
            "estimated_time": "unknown"
        }
    
    def _extract_tasks(self, plan_text: str) -> List[Dict[str, Any]]:
        """从规划文本中提取任务列表"""
        # 简单的任务提取逻辑，可以根据需要优化
        lines = plan_text.split('\n')
        tasks = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('1.') or line.startswith('2.') or 
                        line.startswith('3.') or line.startswith('4.') or
                        line.startswith('5.') or line.startswith('-')):
                tasks.append({
                    "description": line,
                    "status": "pending",
                    "priority": "medium"
                })
        
        return tasks
