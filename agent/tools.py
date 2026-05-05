# agent/tools.py
import datetime


def get_current_time() -> str:
    """获取当前的日期和时间"""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def calculate(expression: str) -> str:
    """计算一个简单的数学表达式，支持 +, -, *, /
    Args:
        expression: 数学表达式字符串，例如 "2 + 3 * 4"
    """
    try:
        # ⚠️ 注意：生产环境严禁直接使用 eval，这里仅用于演示原理
        # 实际项目中建议使用 ast.literal_eval 或专门的数学库
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误: {str(e)}"

# 工具描述映射（OpenAI 兼容格式）
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "当用户询问当前时间、日期或星期几时调用此工具",
            "parameters": {
                "type": "object",
                "properties": {}, # 该工具不需要参数
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "当用户需要进行数学计算时调用此工具",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "需要计算的数学表达式，只包含数字和运算符"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

# 本地函数映射表：将模型返回的工具名映射到实际 Python 函数
AVAILABLE_FUNCTIONS = {
    "get_current_time": get_current_time,
    "calculate": calculate,
}