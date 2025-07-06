"""
测试员智能体 - 负责单元测试编写和代码测试
"""

import os
import subprocess
import sys
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models import BaseLanguageModel
from .base_agent import BaseAgent


class TesterAgent(BaseAgent):
    """测试员智能体"""
    
    def __init__(self, llm: BaseLanguageModel):
        system_prompt = """你是一个专业的软件测试工程师。你的任务是：
1. 分析给定的代码
2. 编写全面的单元测试
3. 测试边界条件和异常情况
4. 使用pytest框架编写测试
5. 确保代码质量和可靠性

请确保：
- 测试覆盖率高
- 包含正常情况和异常情况的测试
- 使用合适的断言
- 测试代码清晰易读
- 遵循测试最佳实践
"""
        super().__init__(
            name="测试员",
            llm=llm,
            description="编写单元测试并执行测试",
            system_prompt=system_prompt
        )
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行测试任务"""
        self.update_state(status="working", current_task=task)
        
        try:
            # 获取生成的代码
            generated_code = context.get("generated_code", {}) if context else {}
            code_content = generated_code.get("code", "")
            
            if not code_content:
                raise ValueError("没有可测试的代码")
            
            # 生成测试代码
            test_result = await self._generate_test_code(code_content, task)
            
            # 执行测试
            execution_result = await self._execute_tests(test_result)
            
            result = {
                "test_code": test_result["test_code"],
                "test_file_path": test_result["test_file_path"],
                "execution_result": execution_result,
                "status": "passed" if execution_result["success"] else "failed"
            }
            
            self.update_state(status="completed", result=result)
            self.set_context("test_result", result)
            
            return result
            
        except Exception as e:
            self.update_state(status="error", error=str(e))
            raise
    
    async def _generate_test_code(self, code: str, task: str) -> Dict[str, Any]:
        """生成测试代码"""
        test_prompt = f"""
{self.system_prompt}

原始代码：
```python
{code}
```

任务描述：{task}

请为上述代码编写完整的单元测试。包括：
1. 导入必要的模块
2. 测试正常功能
3. 测试边界条件
4. 测试异常情况
5. 使用pytest框架

请用```python开始测试代码，```结束。
"""
        
        # 添加用户消息
        self.add_message(HumanMessage(content=test_prompt))
        
        # 调用LLM生成测试代码
        response = await self.llm.ainvoke(self.state.messages)
        self.add_message(response)
        
        # 解析测试代码
        test_code = self._parse_test_code(response.content)
        
        # 保存测试代码到文件
        test_file_path = await self._save_test_to_file(test_code, task)
        
        return {
            "test_code": test_code,
            "test_file_path": test_file_path,
            "raw_response": response.content
        }
    
    def _parse_test_code(self, response_text: str) -> str:
        """从回复中解析测试代码"""
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
        
        return '\n'.join(code_lines)
    
    async def _save_test_to_file(self, test_code: str, task: str) -> str:
        """保存测试代码到文件"""
        # 创建测试目录
        test_dir = "tests"
        os.makedirs(test_dir, exist_ok=True)
        
        # 生成测试文件名
        test_filename = self._generate_test_filename(task)
        test_file_path = os.path.join(test_dir, test_filename)
        
        # 写入测试文件
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        return test_file_path
    
    def _generate_test_filename(self, task: str) -> str:
        """根据任务生成测试文件名"""
        clean_task = "".join(c for c in task if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_task = clean_task.replace(' ', '_').lower()
        return f"test_{clean_task[:40]}.py"
    
    async def _execute_tests(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试"""
        test_file_path = test_result["test_file_path"]
        
        try:
            # 使用pytest执行测试
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file_path, "-v"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "测试执行超时",
                "return_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1
            }
