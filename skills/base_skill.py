# skills/base_skill.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class SkillTool(BaseModel):
    """单个工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    
class BaseSkill(ABC):
    """技能基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称（唯一标识）"""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """技能描述（用于 System Prompt 注入）"""
        pass
        
    @abstractmethod
    def get_tools(self) -> List[Dict]:
        """返回该技能提供的所有工具（OpenAI 兼容格式）"""
        pass
        
    @abstractmethod
    def execute(self, tool_name: str, arguments: Dict) -> Any:
        """执行具体工具"""
        pass