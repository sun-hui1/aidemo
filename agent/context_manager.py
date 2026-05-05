# agent/context_manager.py
import tiktoken
from utils.logger import get_logger
logger = get_logger(__name__)
class ContextManager:
    def __init__(self, max_tokens: int = 4000, model: str = "your_model_name"):
        self.encoder = tiktoken.encoding_for_model(model)
        self.max_tokens = max_tokens
        self.history: list[dict] = []

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        self._trim()

    def get_messages(self) -> list[dict]:
        return self.history.copy()

    def _trim(self):
        logger.info(f"Current context length: {len(self.encoder.encode(self.history[-1]['content']))}")
        # 保留 system prompt，从后向前截断
        total = sum(len(self.encoder.encode(m["content"])) for m in self.history)
        while len(self.history) > 1 and total > self.max_tokens:
            temp =  self.history.pop(1)  # 移除最早的非 system 消息
            logger.info(f"Trimming context: {temp}")
            total = sum(len(self.encoder.encode(m["content"])) for m in self.history)

    # agent/context_manager.py (新增方法)
    def add_assistant_message_with_tool_calls(self, assistant_message: dict):
        """添加包含工具调用的助手消息到历史消息"""
        self.history.append(assistant_message)
        self._trim() # 同样需要检查 Token 限制

    def add_tool_response(self, tool_call_id: str, tool_name: str, content: str):
        """添加工具执行结果到历史消息"""
        self.history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": content
        })
        self._trim() # 同样需要检查 Token 限制