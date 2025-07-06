"""
调试器智能体 - 负责代码调试和错误修复
"""

import ast
import sys
from typing import Any, Dict, List, Optional, Tuple
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models import BaseLanguageModel
from .base_agent import BaseAgent


class DebuggerAgent(BaseAgent):
    """调试器智能体"""
    
    def __init__(self, llm: BaseLanguageModel):
        system_prompt = """你是一个专业的代码调试专家。你的任务是：
1. 分析测试失败的原因
2. 识别代码中的bug和问题
3. 提供具体的修复建议
4. 生成修复后的代码
5. 确保修复不会引入新的问题

请确保：
- 准确识别问题根源
- 提供清晰的修复思路
- 修复后的代码保持原有功能
- 考虑边界条件
- 遵循最佳实践
"""
        super().__init__(
            name="调试器",
            llm=llm,
            description="分析错误并修复代码",
            system_prompt=system_prompt
        )
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行调试任务"""
        self.update_state(status="working", current_task=task)
        
        try:
            # 获取测试结果和代码
            test_result = context.get("test_result", {}) if context else {}
            generated_code = context.get("generated_code", {}) if context else {}
            
            if not test_result or test_result.get("status") == "passed":
                return {"status": "no_debugging_needed", "message": "测试通过，无需调试"}
            
            # 分析错误
            error_analysis = await self._analyze_errors(
                generated_code.get("code", ""),
                test_result.get("execution_result", {})
            )
            
            # 生成修复代码
            fixed_code = await self._generate_fixed_code(
                generated_code.get("code", ""),
                error_analysis,
                task
            )
            
            # 静态分析修复后的代码
            static_analysis = self._static_code_analysis(fixed_code)
            
            result = {
                "error_analysis": error_analysis,
                "fixed_code": fixed_code,
                "static_analysis": static_analysis,
                "status": "fixed"
            }
            
            self.update_state(status="completed", result=result)
            self.set_context("debug_result", result)
            
            return result
            
        except Exception as e:
            self.update_state(status="error", error=str(e))
            raise
    
    async def _analyze_errors(self, code: str, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析错误"""
        error_analysis_prompt = f"""
{self.system_prompt}

原始代码：
```python
{code}
```

测试执行结果：
- 成功: {execution_result.get('success', False)}
- 标准输出: {execution_result.get('stdout', '')}
- 错误输出: {execution_result.get('stderr', '')}
- 返回码: {execution_result.get('return_code', 0)}

请分析这些错误的原因，并提供详细的错误分析报告。包括：
1. 错误类型和位置
2. 错误产生的原因
3. 修复思路和建议
4. 需要注意的问题
"""
        
        # 添加用户消息
        self.add_message(HumanMessage(content=error_analysis_prompt))
        
        # 调用LLM分析错误
        response = await self.llm.ainvoke(self.state.messages)
        self.add_message(response)
        
        return {
            "analysis": response.content,
            "errors": execution_result.get('stderr', ''),
            "success": execution_result.get('success', False)
        }
    
    async def _generate_fixed_code(self, original_code: str, error_analysis: Dict[str, Any], task: str) -> str:
        """生成修复后的代码"""
        fix_prompt = f"""
{self.system_prompt}

原始代码：
```python
{original_code}
```

错误分析：
{error_analysis.get('analysis', '')}

任务描述：{task}

请根据错误分析，生成修复后的完整代码。确保：
1. 修复所有识别的问题
2. 保持原有功能不变
3. 代码结构清晰
4. 添加必要的错误处理

请用```python开始修复后的代码，```结束。
"""
        
        # 添加用户消息
        self.add_message(HumanMessage(content=fix_prompt))
        
        # 调用LLM生成修复代码
        response = await self.llm.ainvoke(self.state.messages)
        self.add_message(response)
        
        # 解析修复后的代码
        fixed_code = self._parse_fixed_code(response.content)
        
        return fixed_code
    
    def _parse_fixed_code(self, response_text: str) -> str:
        """从回复中解析修复后的代码"""
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
    
    def _static_code_analysis(self, code: str) -> Dict[str, Any]:
        """静态代码分析"""
        analysis_result = {
            "syntax_valid": False,
            "issues": [],
            "suggestions": []
        }
        
        try:
            # 检查语法是否正确
            ast.parse(code)
            analysis_result["syntax_valid"] = True
            
            # 简单的代码质量检查
            lines = code.split('\n')
            for i, line in enumerate(lines, 1):
                # 检查行长度
                if len(line) > 100:
                    analysis_result["issues"].append(f"第{i}行过长: {len(line)}字符")
                
                # 检查是否有TODO或FIXME
                if 'TODO' in line or 'FIXME' in line:
                    analysis_result["issues"].append(f"第{i}行包含TODO/FIXME")
            
            # 检查是否有文档字符串
            if '"""' not in code and "'''" not in code:
                analysis_result["suggestions"].append("建议添加文档字符串")
            
        except SyntaxError as e:
            analysis_result["syntax_valid"] = False
            analysis_result["issues"].append(f"语法错误: {str(e)}")
        
        return analysis_result
