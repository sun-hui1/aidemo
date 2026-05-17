# agent/context_manager.py
import tiktoken
from core.memory_store import MemoryStore
from utils.logger import get_logger
import json

logger = get_logger(__name__)
class ContextManager:
    def __init__(self,  session_id: str = "default",max_tokens: int = 4000, model: str = "your_model_name"):
        self.encoder = tiktoken.encoding_for_model(model)
        self.session_id = session_id
        self.max_tokens = max_tokens
        self.history: list[dict] = []
        self.store = MemoryStore()
        # 初始化时从数据库加载历史
        self._load_from_db()
    def _load_from_db(self):
        """从数据库加载历史到内存"""
        db_messages = self.store.load_history(self.session_id)
        self.history = db_messages
        logger.info(f"📂 已加载会话 {self.session_id} 的 {len(self.history)} 条历史消息")
    def add_message(self, role: str, content: str, tool_call_id: str = None, tool_name: str = None):
        """添加消息并同步到数据库"""
        msg = {"role": role, "content": content}

        if tool_call_id:
            msg["tool_call_id"] = tool_call_id
        if tool_name:
            msg["tool_name"] = tool_name
        self.history.append(msg)

        # 同步写入数据库
        self.store.save_message(
            self.session_id, role, content, tool_call_id, tool_name
        )
        self._trim()

    def get_messages(self) -> list[dict]:
        return self.history.copy()

    def set_system_message(self, content: str):
        """设置或更新系统消息（始终保持在索引0且不参与trim）"""
        if self.history and self.history[0]['role'] == 'system':
            self.history[0]['content'] = content
        else:
            self.history.insert(0, {"role": "system", "content": content})

    def _token_count(self, msg: dict) -> int:
        """安全计算单条消息的 token 数，处理 content 为 None 的情况"""
        content = msg.get("content")
        if content is None:
            return 0
        return len(self.encoder.encode(str(content)))

    def _trim(self):
        total = sum(self._token_count(m) for m in self.history)
        while len(self.history) > 1 and total > self.max_tokens:
            removed = self.history.pop(1)
            logger.info(f"Trimming context: {removed}")
            # 如果移除的是带 tool_calls 的 assistant 消息，
            # 则需要一并移除后续孤立的 tool 响应消息
            if removed.get("role") == "assistant" and removed.get("tool_calls"):
                while len(self.history) > 1 and self.history[1].get("role") == "tool":
                    orphan = self.history.pop(1)
                    logger.info(f"Trimming orphaned tool response: {orphan}")
            total = sum(self._token_count(m) for m in self.history)

    # agent/context_manager.py (新增方法)
    def add_assistant_with_tools(self, message_dict: dict):
        """
        专门用于保存模型返回的包含 tool_calls 的 assistant 消息
        :param message_dict: 模型原始返回的 message 字典
        """
        tool_calls = message_dict.get("tool_calls", [])
        # 将 tool_calls 序列化为 JSON 存入数据库
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        
        # 存入内存
        self.history.append(message_dict)
        
        # 存入数据库
        self.store.save_message(
            session_id=self.session_id,
            role="assistant",
            content=message_dict.get("content", ""),
            tool_calls_json=tool_calls_json
        )
        logger.info(f"💾 已保存 Assistant 消息 (含 {len(tool_calls)} 个工具调用)")

    def add_tool_response(self, tool_call_id: str, tool_name: str, content: str):
        """添加工具执行结果到历史消息"""
        self.add_message("tool", content, tool_call_id=tool_call_id, tool_name=tool_name)