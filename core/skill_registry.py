# core/skill_registry.py
import importlib
import inspect
import os
from pathlib import Path
from typing import Dict, Type
from skills.base_skill import BaseSkill
from utils.logger import get_logger

logger = get_logger(__name__)

class SkillRegistry:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills: Dict[str, BaseSkill] = {}
        return cls._instance

    def register(self, skill_class: Type[BaseSkill]):
        """手动注册技能类"""
        skill = skill_class()
        if skill.name in self._skills:
            logger.warning(f"⚠️ 技能 {skill.name} 已存在，将被覆盖")
        self._skills[skill.name] = skill
        logger.info(f"✅ 技能已注册: {skill.name} - {skill.description}")

    def auto_discover(self, skills_dir: str = "skills"):
        """自动扫描目录并注册"""
        skills_path = Path(skills_dir)
        if not skills_path.exists():
            logger.warning(f"📁 技能目录不存在: {skills_dir}")
            return
            
        for file in skills_path.glob("*.py"):
            if file.name.startswith("_"):
                continue
                
            module_name = f"skills.{file.stem}"
            try:
                module = importlib.import_module(module_name)
                # 查找继承自 BaseSkill 的类
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseSkill) and obj != BaseSkill:
                        self.register(obj)
            except Exception as e:
                logger.error(f"❌ 加载技能 {module_name} 失败: {e}")

    def get_all_tools(self) -> list:
        """聚合所有技能的工具列表"""
        all_tools = []
        for skill in self._skills.values():
            all_tools.extend(skill.get_tools())
        return all_tools

    def dispatch(self, tool_name: str, arguments: dict):
        """路由执行：根据工具名找到对应技能并执行"""
        # 工具名格式建议：skill_name_tool_name
        parts = tool_name.split("_", 1)
        if len(parts) != 2:
            raise ValueError(f"无效的工具名格式: {tool_name}，应为 skill_tool")
            
        skill_name, actual_tool = parts
        if skill_name not in self._skills:
            raise ValueError(f"未找到技能: {skill_name}")
            
        return self._skills[skill_name].execute(actual_tool, arguments)