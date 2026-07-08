# skills/base_skill.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SkillTool(BaseModel):
    """单个工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]

class SkillResult(BaseModel):
    """技能执行结果"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: str = ""

class BaseSkill(ABC):
    """技能基类"""
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self._name = name
        self._description = description
        self._version = version
    
    @property
    def name(self) -> str:
        """技能名称（唯一标识）"""
        return self._name
        
    @property
    def description(self) -> str:
        """技能描述（用于 System Prompt 注入）"""
        return self._description
    
    @property
    def version(self) -> str:
        """技能版本"""
        return self._version
        
    @abstractmethod
    def get_tools(self) -> List[Dict]:
        """返回该技能提供的所有工具（OpenAI 兼容格式）"""
        pass
    
    @abstractmethod
    def call(self, tool_name: str, **kwargs) -> SkillResult:
        """执行具体工具"""
        pass
    
    def execute(self, tool_name: str, arguments: Dict) -> Any:
        """兼容旧版本的 execute 方法"""
        return self.call(tool_name, **arguments)