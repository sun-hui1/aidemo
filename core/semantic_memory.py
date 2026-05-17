# core/semantic_memory.py
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from utils.logger import get_logger
logger = get_logger(__name__)

class SemanticMemory:
    def __init__(self, persist_directory="./chroma_db"):
        # 1. 初始化 ChromaDB 客户端（持久化到本地文件夹）
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # 2. 获取或创建集合（Collection）
        self.collection = self.client.get_or_create_collection(name="agent_memories")
        
        # 3. 加载本地 Embedding 模型 (使用轻量级的 all-MiniLM-L6-v2)
        logger.info("🧠 正在加载 Embedding 模型...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Embedding 模型加载完成")

    def add_memory(self, session_id: str, text: str):
        """
        将一段文本转化为向量并存入数据库
        :param session_id: 用于隔离不同用户的记忆
        :param text: 需要记忆的文本内容
        """
        # 生成唯一 ID
        memory_id = f"{session_id}_{self.collection.count() + 1}"
        
        # 生成向量
        embedding = self.model.encode(text).tolist()
        
        # 存入 ChromaDB
        self.collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            metadatas=[{"session_id": session_id, "type": "dialogue"}],
            documents=[text]
        )
        logger.debug(f"💾 已存入记忆: {text[:30]}...")

    def search_memories(self, session_id: str, query: str, top_k: int = 3) -> list:
        """
        根据查询语句，检索最相关的历史记忆
        :return: 相关的文本列表
        """
        # 生成查询向量
        query_embedding = self.model.encode(query).tolist()
        
        # 执行向量搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"session_id": session_id} # 只查当前会话的记忆
        )
        
        # 提取文档内容
        if results['documents'] and results['documents'][0]:
            memories = results['documents'][0]
            logger.info(f"🔍 检索到 {len(memories)} 条相关记忆")
            return memories
        return []