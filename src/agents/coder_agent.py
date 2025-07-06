"""
程序员智能体 - 负责代码生成和实现
"""

import os
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models import BaseLanguageModel
from .base_agent import BaseAgent


class CoderAgent(BaseAgent):
    """程序员智能体"""
    
    def __init__(self, llm: BaseLanguageModel):
        system_prompt = """你是一个专业的Python程序员。你的任务是：
1. 根据需求和计划编写高质量的Python代码
2. 遵循PEP 8代码规范
3. 编写清晰、可读的代码
4. 包含适当的错误处理
5. 添加必要的注释和文档字符串

请确保：
- 代码结构清晰
- 函数和类命名规范
- 包含类型注解
- 处理边界条件
- 代码可测试
"""
        super().__init__(
            name="程序员",
            llm=llm,
            description="根据需求生成Python代码",
            system_prompt=system_prompt
        )
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行编码任务"""
        self.update_state(status="working", current_task=task)
        
        try:
            # 获取规划上下文
            plan = context.get("plan", {}) if context else {}
            
            # 构建编码提示
            coding_prompt = f"""
{self.system_prompt}

开发任务：{task}

{f"开发计划：{plan.get('raw_plan', '')}" if plan else ""}

请编写完整的Python代码实现。包括：
1. 主要功能代码
2. 错误处理
3. 文档字符串
4. 类型注解
5. 示例用法

请用```python开始代码块，```结束。
"""
            
            # 添加用户消息
            self.add_message(HumanMessage(content=coding_prompt))
            
            # 调用LLM生成代码
            response = await self.llm.ainvoke(self.state.messages)
            self.add_message(response)
            
            # 解析代码
            code_result = self._parse_code(response.content)
            
            # 保存代码到文件
            if code_result["code"]:
                file_path = await self._save_code_to_file(code_result["code"], task)
                code_result["file_path"] = file_path
            
            self.update_state(status="completed", result=code_result)
            self.set_context("generated_code", code_result)
            
            return code_result
            
        except Exception as e:
            self.update_state(status="error", error=str(e))
            raise
    
    def _parse_code(self, response_text: str) -> Dict[str, Any]:
        """从回复中解析代码"""
        lines = response_text.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```python'):
                in_code_block = True
                continue
            elif line.strip() == '```' and in_code_block:
                in_code_block = False
                continue
            elif in_code_block:
                code_lines.append(line)
        
        code = '\n'.join(code_lines)
        
        return {
            "code": code,
            "raw_response": response_text,
            "language": "python",
            "status": "generated"
        }
    
    async def _save_code_to_file(self, code: str, task: str) -> str:
        """保存代码到文件"""
        # 创建输出目录
        output_dir = "generated_code"
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        filename = self._generate_filename(task)
        file_path = os.path.join(output_dir, filename)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return file_path
    
    def _generate_filename(self, task: str) -> str:
        """根据任务生成文件名"""
        # 简单的文件名生成逻辑
        clean_task = "".join(c for c in task if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_task = clean_task.replace(' ', '_').lower()
        return f"{clean_task[:50]}.py"
