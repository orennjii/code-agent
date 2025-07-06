"""
主应用入口
"""

import os
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseLanguageModel

from .workflow import WorkflowGraph
from .config import Config


class MultiAgentWorkflow:
    """多智能体工作流主类"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.llm = self._init_llm()
        self.workflow_graph = WorkflowGraph(self.llm, self.config.max_iterations)
    
    def _init_llm(self) -> BaseLanguageModel:
        """初始化语言模型"""
        return ChatGoogleGenerativeAI(
            model=self.config.llm_model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            google_api_key=self.config.google_api_key
        )
    
    async def execute_workflow(self, user_request: str, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """执行工作流"""
        return await self.workflow_graph.execute(user_request, workflow_id)
    
    def get_workflow_structure(self) -> Dict[str, Any]:
        """获取工作流结构"""
        return self.workflow_graph.get_graph_structure()
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            "llm_model": self.config.llm_model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "max_iterations": self.config.max_iterations,
            "timeout": self.config.timeout
        }


async def main():
    """主函数示例"""
    # 创建工作流实例
    workflow = MultiAgentWorkflow()
    
    # 示例用户请求
    user_request = "实现一个快速排序算法"
    
    print("🚀 多智能体协作系统启动")
    print("=" * 50)
    
    # 执行工作流
    result = await workflow.execute_workflow(user_request)
    
    print("=" * 50)
    print("📊 执行结果:")
    print(f"成功: {result['success']}")
    print(f"工作流ID: {result.get('workflow_id')}")
    print(f"状态: {result.get('status')}")
    print(f"迭代次数: {result.get('iteration_count')}")
    print(f"完成任务: {result.get('completed_tasks')}")
    print(f"失败任务: {result.get('failed_tasks')}")
    
    if result.get('final_code'):
        print("\n📄 生成的代码:")
        print("-" * 30)
        print(result['final_code'])
    
    if result.get('error_history'):
        print("\n❌ 错误历史:")
        for error in result['error_history']:
            print(f"  - {error}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
