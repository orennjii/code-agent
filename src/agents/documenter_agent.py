"""
文档工程师智能体 - 负责代码文档生成和注释
"""

import os
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models import BaseLanguageModel
from .base_agent import BaseAgent


class DocumenterAgent(BaseAgent):
    """文档工程师智能体"""
    
    def __init__(self, llm: BaseLanguageModel):
        system_prompt = """你是一个专业的技术文档工程师。你的任务是：
1. 为代码生成清晰的文档
2. 编写详细的API文档
3. 创建使用示例
4. 生成README文件
5. 确保文档的准确性和完整性

请确保：
- 文档结构清晰
- 包含使用示例
- 解释复杂的概念
- 遵循文档最佳实践
- 使用Markdown格式
"""
        super().__init__(
            name="文档工程师",
            llm=llm,
            description="生成代码文档和说明",
            system_prompt=system_prompt
        )
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行文档生成任务"""
        self.update_state(status="working", current_task=task)
        
        try:
            # 获取最终代码（可能是修复后的代码）
            final_code = self._get_final_code(context)
            
            if not final_code:
                raise ValueError("没有可文档化的代码")
            
            # 生成API文档
            api_doc = await self._generate_api_documentation(final_code, task)
            
            # 生成README文件
            readme = await self._generate_readme(final_code, task, context)
            
            # 生成使用示例
            examples = await self._generate_examples(final_code, task)
            
            # 保存文档
            doc_paths = await self._save_documentation(api_doc, readme, examples, task)
            
            result = {
                "api_documentation": api_doc,
                "readme": readme,
                "examples": examples,
                "file_paths": doc_paths,
                "status": "completed"
            }
            
            self.update_state(status="completed", result=result)
            self.set_context("documentation", result)
            
            return result
            
        except Exception as e:
            self.update_state(status="error", error=str(e))
            raise
    
    def _get_final_code(self, context: Optional[Dict[str, Any]]) -> str:
        """获取最终代码（优先使用修复后的代码）"""
        if not context:
            return ""
        
        # 优先使用调试后的代码
        debug_result = context.get("debug_result", {})
        if debug_result and debug_result.get("fixed_code"):
            return debug_result["fixed_code"]
        
        # 否则使用原始生成的代码
        generated_code = context.get("generated_code", {})
        return generated_code.get("code", "")
    
    async def _generate_api_documentation(self, code: str, task: str) -> str:
        """生成API文档"""
        api_doc_prompt = f"""
{self.system_prompt}

代码：
```python
{code}
```

任务描述：{task}

请为上述代码生成详细的API文档。包括：
1. 模块/类/函数的描述
2. 参数说明
3. 返回值说明
4. 异常说明
5. 使用注意事项

请使用Markdown格式。
"""
        
        # 添加用户消息
        self.add_message(HumanMessage(content=api_doc_prompt))
        
        # 调用LLM生成API文档
        response = await self.llm.ainvoke(self.state.messages)
        self.add_message(response)
        
        return response.content
    
    async def _generate_readme(self, code: str, task: str, context: Optional[Dict[str, Any]]) -> str:
        """生成README文件"""
        # 获取额外信息
        plan = context.get("plan", {}) if context else {}
        test_result = context.get("test_result", {}) if context else {}
        
        readme_prompt = f"""
{self.system_prompt}

代码：
```python
{code}
```

任务描述：{task}
开发计划：{plan.get('raw_plan', '无') if plan else '无'}
测试状态：{test_result.get('status', '未知') if test_result else '未知'}

请生成一个完整的README.md文件。包括：
1. 项目标题和描述
2. 功能特性
3. 安装说明
4. 使用方法
5. API文档链接
6. 测试信息
7. 贡献指南
8. 许可证信息

请使用标准的Markdown格式。
"""
        
        # 添加用户消息
        self.add_message(HumanMessage(content=readme_prompt))
        
        # 调用LLM生成README
        response = await self.llm.ainvoke(self.state.messages)
        self.add_message(response)
        
        return response.content
    
    async def _generate_examples(self, code: str, task: str) -> str:
        """生成使用示例"""
        examples_prompt = f"""
{self.system_prompt}

代码：
```python
{code}
```

任务描述：{task}

请生成详细的使用示例。包括：
1. 基本使用示例
2. 高级用法示例
3. 错误处理示例
4. 性能优化建议
5. 常见问题解答

请使用Markdown格式，包含可运行的代码示例。
"""
        
        # 添加用户消息
        self.add_message(HumanMessage(content=examples_prompt))
        
        # 调用LLM生成示例
        response = await self.llm.ainvoke(self.state.messages)
        self.add_message(response)
        
        return response.content
    
    async def _save_documentation(self, api_doc: str, readme: str, examples: str, task: str) -> Dict[str, str]:
        """保存文档到文件"""
        # 创建文档目录
        docs_dir = "docs"
        os.makedirs(docs_dir, exist_ok=True)
        
        # 生成文件名前缀
        clean_task = "".join(c for c in task if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_task = clean_task.replace(' ', '_').lower()[:30]
        
        # 保存文件
        file_paths = {}
        
        # API文档
        api_doc_path = os.path.join(docs_dir, f"{clean_task}_api.md")
        with open(api_doc_path, 'w', encoding='utf-8') as f:
            f.write(api_doc)
        file_paths["api_doc"] = api_doc_path
        
        # README
        readme_path = os.path.join(docs_dir, f"{clean_task}_README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme)
        file_paths["readme"] = readme_path
        
        # 示例
        examples_path = os.path.join(docs_dir, f"{clean_task}_examples.md")
        with open(examples_path, 'w', encoding='utf-8') as f:
            f.write(examples)
        file_paths["examples"] = examples_path
        
        return file_paths
