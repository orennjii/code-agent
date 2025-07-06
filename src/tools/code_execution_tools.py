"""
代码执行工具
"""

import subprocess
import sys
import tempfile
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class CodeExecutionTools:
    """代码执行工具类"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def execute_python_code(self, code: str, input_data: Optional[str] = None) -> Dict[str, Any]:
        """执行Python代码"""
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            try:
                # 执行代码
                result = subprocess.run(
                    [sys.executable, temp_file_path],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "execution_time": "unknown"
                }
            finally:
                # 清理临时文件
                os.unlink(temp_file_path)
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "执行超时",
                "return_code": -1,
                "execution_time": f">{self.timeout}s"
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "execution_time": "unknown"
            }
    
    def run_tests(self, test_file_path: str, test_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """运行测试"""
        try:
            # 构建pytest命令
            cmd = [sys.executable, "-m", "pytest", test_file_path]
            if test_args:
                cmd.extend(test_args)
            else:
                cmd.extend(["-v", "--tb=short"])
            
            # 执行测试
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "test_passed": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "测试执行超时",
                "return_code": -1,
                "test_passed": False
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "test_passed": False
            }
    
    def lint_code(self, file_path: str) -> Dict[str, Any]:
        """代码风格检查"""
        try:
            # 使用flake8进行代码检查
            result = subprocess.run(
                [sys.executable, "-m", "flake8", file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "has_issues": result.returncode != 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "代码检查超时",
                "return_code": -1,
                "has_issues": True
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "has_issues": True
            }
    
    def format_code(self, file_path: str) -> Dict[str, Any]:
        """格式化代码"""
        try:
            # 使用black格式化代码
            result = subprocess.run(
                [sys.executable, "-m", "black", file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "formatted": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "代码格式化超时",
                "return_code": -1,
                "formatted": False
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "formatted": False
            }
    
    def type_check(self, file_path: str) -> Dict[str, Any]:
        """类型检查"""
        try:
            # 使用mypy进行类型检查
            result = subprocess.run(
                [sys.executable, "-m", "mypy", file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "type_issues": result.returncode != 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "类型检查超时",
                "return_code": -1,
                "type_issues": True
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "type_issues": True
            }
    
    def install_package(self, package_name: str) -> Dict[str, Any]:
        """安装Python包"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "package": package_name
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "包安装超时",
                "return_code": -1,
                "package": package_name
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "package": package_name
            }
