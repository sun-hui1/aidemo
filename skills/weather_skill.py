# skills/weather_skill.py
from skills.base_skill import BaseSkill, SkillTool
from typing import List, Dict
import requests
import random

class WeatherSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "weather"
        
    @property
    def description(self) -> str:
        return "提供全球城市天气查询功能。支持实时温度、湿度和风速。"
        
    def get_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "weather_get_current",
                    "description": "获取指定城市的实时天气",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "城市名称，如北京、London"}
                        },
                        "required": ["city"]
                    }
                }
            }
        ]
        
    def execute(self, tool_name: str, arguments: Dict) -> str:
        if tool_name == "get_current":
            city = arguments.get("city", "未知城市")
            # 模拟 API 调用（实际可接 OpenWeatherMap）
            temp = random.randint(15, 35)
            condition = random.choice(["晴", "多云", "小雨"])
            return f"{city} 当前天气：{condition}，气温 {temp}°C"
        raise ValueError(f"未知工具: {tool_name}")