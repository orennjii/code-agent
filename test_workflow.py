"""
测试LangGraph工作流的完整示例
"""

import asyncio
import os
from src.main import MultiAgentWorkflow
from src.config import Config


async def test_langgraph_workflow():
    """测试LangGraph工作流"""
    print("🧪 测试LangGraph工作流")
    print("=" * 60)
    
    # 检查API密钥
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ 错误：请设置GOOGLE_API_KEY环境变量")
        print("1. 复制 .env.example 为 .env")
        print("2. 在 .env 文件中设置您的Google API密钥")
        print("3. 获取API密钥：https://ai.google.dev/")
        return
    
    # 创建配置
    config = Config(
        llm_model="gemini-2.5-pro",
        temperature=0.3,  # 较低温度以获得更稳定的结果
        max_tokens=65536,
        max_iterations=2  # 减少迭代次数以便快速测试
    )
    
    print(f"🔧 配置信息:")
    print(f"模型: {config.llm_model}")
    print(f"温度: {config.temperature}")
    print(f"最大令牌: {config.max_tokens}")
    print(f"最大迭代: {config.max_iterations}")
    print()
    
    # 创建工作流实例
    workflow = MultiAgentWorkflow(config)
    
    # 显示工作流结构
    structure = workflow.get_workflow_structure()
    print("📊 工作流结构:")
    print(f"节点: {structure['nodes']}")
    print(f"入口点: {structure['entry_point']}")
    print(f"描述: {structure['description']}")
    print()
    
    # 测试用例
    test_cases = [
        {
            "name": "简单函数",
            "request": "实现一个计算两个数字之和的函数，包含基本的错误处理"
        },
        # 可以添加更多测试用例
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🚀 测试用例 {i}: {test_case['name']}")
        print(f"请求: {test_case['request']}")
        print("-" * 50)
        
        try:
            # 执行工作流
            result = await workflow.execute_workflow(test_case['request'])
            
            # 显示结果
            print("\n📋 执行结果:")
            print(f"✅ 成功: {result['success']}")
            print(f"📊 状态: {result['status']}")
            print(f"🔄 迭代次数: {result['iteration_count']}")
            print(f"✓ 完成任务: {result['completed_tasks']}")
            print(f"✗ 失败任务: {result['failed_tasks']}")
            
            if result.get('final_code'):
                print(f"\n📝 生成的代码:")
                print("```python")
                print(result['final_code'])
                print("```")
            
            if result.get('final_documentation'):
                print(f"\n📚 生成的文档:")
                doc = result['final_documentation']
                # 只显示前500个字符
                if len(doc) > 500:
                    print(doc[:500] + "...")
                else:
                    print(doc)
            
            if result.get('error_history'):
                print(f"\n⚠️ 错误历史:")
                for error in result['error_history']:
                    print(f"  - {error}")
            
            print("\n" + "=" * 60)
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            print("=" * 60)


async def test_graph_visualization():
    """测试图可视化"""
    print("📊 测试图可视化")
    print("-" * 30)
    
    try:
        config = Config()
        workflow = MultiAgentWorkflow(config)
        workflow.workflow_graph.visualize()
    except Exception as e:
        print(f"可视化失败: {e}")


async def main():
    """主函数"""
    print("🧪 LangGraph多智能体工作流测试套件")
    print("使用Google Gemini模型")
    print("=" * 60)
    
    # 测试图可视化
    await test_graph_visualization()
    print()
    
    # 测试完整工作流
    await test_langgraph_workflow()
    
    print("🎉 测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
