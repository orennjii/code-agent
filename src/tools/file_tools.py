"""
文件操作工具
"""

import os
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path


class FileTools:
    """文件操作工具类"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def create_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """创建文件"""
        try:
            full_path = self.base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "path": str(full_path),
                "message": f"文件创建成功: {file_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"文件创建失败: {file_path}"
            }
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """读取文件"""
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": "文件不存在",
                    "content": ""
                }
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "path": str(full_path)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }
    
    def update_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """更新文件内容"""
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": "文件不存在",
                    "message": f"文件不存在: {file_path}"
                }
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "path": str(full_path),
                "message": f"文件更新成功: {file_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"文件更新失败: {file_path}"
            }
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """删除文件"""
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": "文件不存在",
                    "message": f"文件不存在: {file_path}"
                }
            
            full_path.unlink()
            
            return {
                "success": True,
                "message": f"文件删除成功: {file_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"文件删除失败: {file_path}"
            }
    
    def list_files(self, directory: str = "") -> Dict[str, Any]:
        """列出目录中的文件"""
        try:
            full_path = self.base_path / directory
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": "目录不存在",
                    "files": []
                }
            
            files = []
            for item in full_path.iterdir():
                files.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            
            return {
                "success": True,
                "files": files,
                "path": str(full_path)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "files": []
            }
    
    def create_directory(self, directory: str) -> Dict[str, Any]:
        """创建目录"""
        try:
            full_path = self.base_path / directory
            full_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "path": str(full_path),
                "message": f"目录创建成功: {directory}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"目录创建失败: {directory}"
            }
    
    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """复制文件"""
        try:
            source_path = self.base_path / source
            dest_path = self.base_path / destination
            
            if not source_path.exists():
                return {
                    "success": False,
                    "error": "源文件不存在",
                    "message": f"源文件不存在: {source}"
                }
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)
            
            return {
                "success": True,
                "source": str(source_path),
                "destination": str(dest_path),
                "message": f"文件复制成功: {source} -> {destination}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"文件复制失败: {source} -> {destination}"
            }
