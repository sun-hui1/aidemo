from core.llm_client import LLMClient
from utils.logger import get_logger
from .context_manager import ContextManager  # 同级模块
from .tools import TOOLS_SCHEMA, AVAILABLE_FUNCTIONS
import json
import uuid
from core.semantic_memory import SemanticMemory
import asyncio
from agent.mcp_tools import MCPToolAdapter

logger = get_logger(__name__)

class SimpleChatAgent:
    def __init__(self ,session_id: str = None, mcp_config: dict = None):
        """
        初始化方法
        初始化LLM客户端实例
        """
        # 如果没有提供 session_id，则生成一个随机的
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.llm = LLMClient()  # 创建LLMClient类的实例并赋值给self.llm属性
        self.context_manager = ContextManager(session_id=self.session_id, max_tokens=4000, model="gpt-4")
        self.memory = SemanticMemory() # 初始化语义记忆
        logger.info(f"🚀 ChatAgent 启动成功, session_id: {self.session_id}")
        # 初始化 MCP 适配器（如果配置了）
        self.mcp_adapter: MCPToolAdapter | None = None
        if mcp_config:
            self.mcp_adapter = MCPToolAdapter(
                server_command=mcp_config["command"],
                server_args=mcp_config.get("args", [])
            )
            # 异步连接（在 run 中首次调用时建立）
            self._mcp_connected = False
    async def _ensure_mcp_connected(self):
        """确保 MCP 已连接（懒加载）"""
        if self.mcp_adapter and not self._mcp_connected:
            await self.mcp_adapter.connect()
            self._mcp_connected = True
    def _merge_tool_schemas(self) -> list[dict]:
        """合并本地工具 + MCP 工具"""
        all_tools = TOOLS_SCHEMA.copy()  # 本地工具
        if self.mcp_adapter and self.mcp_adapter.tools_schema:
            all_tools.extend(self.mcp_adapter.tools_schema)
        return all_tools
    


    # 支持并行工具调用与重试        
    async def run(self, user_input: str) -> str:
        # === 1. 记忆检索与构造 ===
        relevant_memories = self.memory.search_memories(self.session_id, user_input)
        #  构造带有“回忆”的 System Prompt
        memory_context = ""
        if relevant_memories:
            memory_str = "\n".join([f"- {m}" for m in relevant_memories])
            memory_context = f"\n【相关历史回忆】:\n{memory_str}\n请结合以上回忆回答用户问题。"
        # 注意：这里我们需要动态修改 System Prompt
        # 简单做法：在 context 的最前面插入一条 system 消息
        system_prompt = f"你是一个有用的助手。{memory_context}"

        # 确保 System Prompt 在历史最前面
        self.context_manager.set_system_message(system_prompt)
        # === 2. 确保 MCP 连接 ===
        await self._ensure_mcp_connected()

        # 输入用户上下文
        self.context_manager.add_message("user", user_input)
        # 设置最大迭代次数，防止模型陷入死循环（比如一直调用工具却不结束）
        max_iterations = 5
        iteration = 0

        # === 3. 主循环 ===
        while iteration < max_iterations:
            iteration += 1
            message = self.context_manager.get_messages()
            # 【关键】合并工具列表
            all_tools = self._merge_tool_schemas()
            # 3、调用模型传入工具定义
            logger.info("开始调用模型")
            try:
                response_data = self.llm.chat_completion_with_tool_retry(message, tools=all_tools)
            except Exception as e:
                return f"❌ 系统繁忙:: {str(e)}"
            
            # 4、解析工具调用
            tool_calls = self.parse_tool_calls(response_data)
            # 5、执行工具调用
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    args = tool_call["arguments"]
                    tool_id = tool_call["id"]
                    # 【关键】区分本地工具 vs MCP 工具
                    if tool_name.startswith("mcp_") and self.mcp_adapter:
                        # 调用 MCP 工具
                        result = await self.mcp_adapter.execute(tool_name, args)
                        logger.info(f"✅ MCP 工具 {tool_name} 执行结果: {result}")
                        self.context_manager.add_tool_response(tool_id, tool_name, str(result))
                    elif tool_name in AVAILABLE_FUNCTIONS:
                        # 执行本地函数
                        try:
                            func = AVAILABLE_FUNCTIONS[tool_name]
                            # 注意：有些工具不需要参数，有些需要
                            if args:
                                result = func(**args)
                            else:
                                result = func()
                            
                            logger.info(f"✅ 工具 {tool_name} 执行结果: {result}")
                            
                            # 将工具执行结果加入上下文
                            # 格式必须严格符合 OpenAI 规范
                            self.context_manager.add_tool_response(tool_id, tool_name, str(result))
                        except Exception as e:
                            error_msg = f"工具执行错误: {str(e)}"
                            logger.error(error_msg)
                            self.context_manager.add_tool_response(tool_id, tool_name, error_msg)
                    else:
                        self.context_manager.add_tool_response(tool_id, tool_name, "错误：未知工具")
                # 关键点：如果有工具调用，必须再次调用 LLM，让它根据结果生成回答
                continue 
            else:
                # 6、没有工具调用，则直接返回模型结果
                assistant_message = response_data["choices"][0]["message"]["content"]
                self.context_manager.add_message("assistant", assistant_message)
                # 4. 【新】对话结束后，将重要的用户输入存入记忆
                # 简单策略：所有用户输入都存，或者过滤掉短指令
                if len(user_input) > 5: 
                    self.memory.add_memory(self.session_id, f"用户说: {user_input}")
                return assistant_message
        return "⚠️ 达到最大尝试次数，任务未完成。"
    def parse_tool_calls(self, response_data) -> list:
        """
        解析模型返回的工具调用请求
        :return: 列表，每个元素包含 tool_name 和 arguments
        """
        choice = response_data["choices"][0]
        message = choice["message"]
        
        # 检查是否有 tool_calls字段
        if "tool_calls" in message and message["tool_calls"]:
            raw_tool_calls = message["tool_calls"]
            logger.info(f"🛠️ 检测到 {len(raw_tool_calls)} 个工具调用请求")
            logger.info(f"📤 模型返回: {str(message)[:200]}...")
            self.context_manager.add_assistant_with_tools(message)
            parsed_tool_calls = []
            for tc in raw_tool_calls:
                function_info = tc["function"]
                parsed_tool_calls.append({
                    "id": tc["id"],
                    "name": function_info["name"],
                    "arguments": json.loads(function_info["arguments"])
                })
            return parsed_tool_calls
        return []

    