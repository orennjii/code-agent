"""
配置管理
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config(BaseModel):
    """配置类"""
    
    # Google Gemini配置
    google_api_key: str = Field(
        default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""),
        description="Google API密钥"
    )
    
    # 模型配置
    llm_model: str = Field(
        default_factory=lambda: os.getenv("LLM_MODEL", "gemini-2.5-pro"),
        description="语言模型名称"
    )
    temperature: float = Field(
        default_factory=lambda: float(os.getenv("TEMPERATURE", 0.7)),
        ge=0.0,
        le=2.0,
        description="模型温度"
    )
    max_tokens: int = Field(
        default_factory=lambda: int(os.getenv("MAX_TOKENS", 16384)),
        gt=0,
        description="最大令牌数"
    )
    
    # 工作流配置
    max_iterations: int = Field(
        default_factory=lambda: int(os.getenv("MAX_ITERATIONS", 3)),
        gt=0,
        description="最大迭代次数"
    )
    timeout: int = Field(
        default_factory=lambda: int(os.getenv("TIMEOUT", 30)),
        gt=0,
        description="超时时间（秒）"
    )
    
    # 输出配置
    output_dir: str = Field(
        default="output",
        description="输出目录"
    )
    save_intermediate_results: bool = Field(
        default=True,
        description="是否保存中间结果"
    )
    
    # 日志配置
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="日志文件路径"
    )
    
    def validate_config(self) -> bool:
        """验证配置"""
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required")
        
        return True
    
    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量创建配置"""
        return cls()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump()
    
    def save_to_file(self, file_path: str) -> None:
        """保存到文件"""
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> "Config":
        """从文件加载配置"""
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
