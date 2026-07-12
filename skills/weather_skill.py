# skills/weather_skill.py
from skills.base_skill import BaseSkill, SkillResult
from typing import List, Dict, Any
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

    def call(self, tool_name: str, **kwargs) -> SkillResult:
        """执行具体的天气操作"""
        try:
            if tool_name == "get_current":
                city = kwargs.get("city", "未知城市")
                # 模拟 API 调用（实际可接 OpenWeatherMap）
                temp = random.randint(15, 35)
                condition = random.choice(["晴", "多云", "小雨"])
                result = f"{city} 当前天气：{condition}，气温 {temp}°C"
                return SkillResult(
                    success=True,
                    data={"city": city, "temperature": temp, "condition": condition},
                    error=None,
                    message=result
                )
            else:
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"未知工具：{tool_name}",
                    message=f"{self.name} 技能不包含此工具"
                )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="天气查询失败"
            )
    
    def execute(self, tool_name: str, arguments: Dict) -> Any:
        """兼容旧版本的 execute 方法"""
        result = self.call(tool_name, **arguments)
        return result.message if result.success else result.error
