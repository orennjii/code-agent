"""
代码分析工具
"""

import ast
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class AnalysisTools:
    """代码分析工具类"""
    
    def __init__(self):
        pass
    
    def analyze_python_code(self, code: str) -> Dict[str, Any]:
        """分析Python代码"""
        try:
            tree = ast.parse(code)
            
            analysis = {
                "syntax_valid": True,
                "classes": [],
                "functions": [],
                "imports": [],
                "complexity": self._calculate_complexity(tree),
                "lines_of_code": len(code.split('\n')),
                "docstrings": self._extract_docstrings(tree),
                "type_hints": self._check_type_hints(tree),
                "issues": []
            }
            
            # 分析AST节点
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis["classes"].append({
                        "name": node.name,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        "line": node.lineno
                    })
                elif isinstance(node, ast.FunctionDef):
                    analysis["functions"].append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "line": node.lineno,
                        "has_docstring": ast.get_docstring(node) is not None
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis["imports"].append({
                                "module": alias.name,
                                "type": "import",
                                "line": node.lineno
                            })
                    else:
                        for alias in node.names:
                            analysis["imports"].append({
                                "module": node.module,
                                "name": alias.name,
                                "type": "from_import",
                                "line": node.lineno
                            })
            
            return analysis
            
        except SyntaxError as e:
            return {
                "syntax_valid": False,
                "error": str(e),
                "line": getattr(e, 'lineno', 0),
                "classes": [],
                "functions": [],
                "imports": [],
                "complexity": 0,
                "lines_of_code": 0,
                "docstrings": [],
                "type_hints": False,
                "issues": [f"语法错误: {str(e)}"]
            }
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """计算代码复杂度"""
        complexity = 1  # 基础复杂度
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def _extract_docstrings(self, tree: ast.AST) -> List[str]:
        """提取文档字符串"""
        docstrings = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring:
                    docstrings.append(docstring)
        
        return docstrings
    
    def _check_type_hints(self, tree: ast.AST) -> bool:
        """检查是否有类型注解"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 检查参数类型注解
                for arg in node.args.args:
                    if arg.annotation:
                        return True
                # 检查返回类型注解
                if node.returns:
                    return True
        
        return False
    
    def check_code_quality(self, code: str) -> Dict[str, Any]:
        """检查代码质量"""
        issues = []
        suggestions = []
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 检查行长度
            if len(line) > 100:
                issues.append(f"第{i}行过长: {len(line)}字符")
            
            # 检查是否有TODO或FIXME
            if re.search(r'\b(TODO|FIXME|XXX)\b', line):
                issues.append(f"第{i}行包含TODO/FIXME标记")
            
            # 检查是否有print语句（可能是调试代码）
            if re.search(r'\bprint\s*\(', line):
                suggestions.append(f"第{i}行包含print语句，考虑使用logging")
            
            # 检查是否有裸露的except
            if re.search(r'\bexcept\s*:', line):
                issues.append(f"第{i}行使用了裸露的except，应该指定异常类型")
        
        return {
            "issues": issues,
            "suggestions": suggestions,
            "total_lines": len(lines),
            "quality_score": max(0, 100 - len(issues) * 10 - len(suggestions) * 5)
        }
    
    def extract_functions_and_classes(self, code: str) -> Dict[str, Any]:
        """提取函数和类的定义"""
        try:
            tree = ast.parse(code)
            
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "line_start": node.lineno,
                        "line_end": node.end_lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node),
                        "decorators": [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
                        "is_async": isinstance(node, ast.AsyncFunctionDef)
                    }
                    functions.append(func_info)
                
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line_start": node.lineno,
                        "line_end": node.end_lineno,
                        "bases": [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases],
                        "docstring": ast.get_docstring(node),
                        "methods": [],
                        "decorators": [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list]
                    }
                    
                    # 提取方法
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                "name": item.name,
                                "line_start": item.lineno,
                                "line_end": item.end_lineno,
                                "args": [arg.arg for arg in item.args.args],
                                "is_property": any(d.id == 'property' if isinstance(d, ast.Name) else False for d in item.decorator_list),
                                "is_static": any(d.id == 'staticmethod' if isinstance(d, ast.Name) else False for d in item.decorator_list),
                                "is_class_method": any(d.id == 'classmethod' if isinstance(d, ast.Name) else False for d in item.decorator_list)
                            }
                            class_info["methods"].append(method_info)
                    
                    classes.append(class_info)
            
            return {
                "functions": functions,
                "classes": classes,
                "total_functions": len(functions),
                "total_classes": len(classes)
            }
            
        except SyntaxError as e:
            return {
                "error": str(e),
                "functions": [],
                "classes": [],
                "total_functions": 0,
                "total_classes": 0
            }
    
    def find_dependencies(self, code: str) -> Dict[str, Any]:
        """查找代码依赖"""
        try:
            tree = ast.parse(code)
            
            standard_libs = set()
            third_party_libs = set()
            local_imports = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        if self._is_standard_library(module_name):
                            standard_libs.add(module_name)
                        else:
                            third_party_libs.add(module_name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        if node.level > 0:  # 相对导入
                            local_imports.add(node.module or '')
                        elif self._is_standard_library(module_name):
                            standard_libs.add(module_name)
                        else:
                            third_party_libs.add(module_name)
            
            return {
                "standard_libraries": sorted(standard_libs),
                "third_party_libraries": sorted(third_party_libs),
                "local_imports": sorted(local_imports),
                "total_dependencies": len(standard_libs) + len(third_party_libs) + len(local_imports)
            }
            
        except SyntaxError as e:
            return {
                "error": str(e),
                "standard_libraries": [],
                "third_party_libraries": [],
                "local_imports": [],
                "total_dependencies": 0
            }
    
    def _is_standard_library(self, module_name: str) -> bool:
        """判断是否为标准库"""
        # 常见的Python标准库模块
        standard_modules = {
            'os', 'sys', 'json', 'datetime', 'time', 'random', 'math', 'collections',
            'itertools', 'functools', 'operator', 're', 'string', 'io', 'pathlib',
            'typing', 'abc', 'asyncio', 'concurrent', 'threading', 'multiprocessing',
            'subprocess', 'shutil', 'tempfile', 'unittest', 'logging', 'argparse',
            'configparser', 'csv', 'sqlite3', 'pickle', 'base64', 'hashlib', 'hmac',
            'urllib', 'http', 'email', 'xml', 'html', 'ast', 'dis', 'inspect'
        }
        
        return module_name in standard_modules
