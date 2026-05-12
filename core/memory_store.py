# core/memory_store.py
import sqlite3
import json
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class MemoryStore:
    def __init__(self, db_path="agent_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表并迁移结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. 创建基础表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                tool_call_id TEXT,
                tool_name TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. 【新增】尝试添加 tool_calls_json 列
        # 如果列已存在，SQLite 会报错，我们用 try-except 忽略它
        try:
            cursor.execute('ALTER TABLE messages ADD COLUMN tool_calls_json TEXT')
            logger.info("📦 数据库结构升级：已添加 tool_calls_json 字段")
        except sqlite3.OperationalError:
            # 如果报错说列已存在，说明已经是最新结构，无需操作
            pass
            
        conn.commit()
        conn.close()
        logger.info(f"💾 数据库初始化完成: {self.db_path}")

    def save_message(self, session_id: str, role: str, content: str, 
                     tool_call_id: str = None, tool_name: str = None, 
                     tool_calls_json: str = None): # 新增参数
        """保存单条消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (session_id, role, content, tool_call_id, tool_name, tool_calls_json)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, role, content, tool_call_id, tool_name, tool_calls_json))
        conn.commit()
        conn.close()

    def load_history(self, session_id: str, limit: int = 50) -> list:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM messages 
            WHERE session_id = ? 
            ORDER BY id ASC 
            LIMIT ?
        ''', (session_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in rows:
            msg = {"role": row["role"]}
            
            # 处理 Assistant 的工具调用
            if row["role"] == "assistant" and row["tool_calls_json"]:
                try:
                    msg["tool_calls"] = json.loads(row["tool_calls_json"])
                    msg["content"] = row["content"] # 通常为空
                except json.JSONDecodeError:
                    logger.error("解析 tool_calls JSON 失败")
            # 处理 Tool 的结果
            elif row["role"] == "tool":
                msg["tool_call_id"] = row["tool_call_id"]
                msg["name"] = row["tool_name"]
                msg["content"] = row["content"]
            else:
                msg["content"] = row["content"]
                
            messages.append(msg)
            
        return messages

    def clear_session(self, session_id: str):
        """清空特定会话的记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()
        logger.info(f"🗑️ 会话 {session_id} 记忆已清空")