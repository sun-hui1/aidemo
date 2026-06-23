from core.llm_client import LLMClient
from utils.logger import get_logger
from .context_manager import ContextManager  # 同级模块
from .tools import TOOLS_SCHEMA, AVAILABLE_FUNCTIONS
import json
import uuid
from core.semantic_memory import SemanticMemory
import asyncio
from agent.mcp_tools import MCPToolAdapter
from typing import Iterator
from core.skill_registry import SkillRegistry

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

        # ✅ 初始化技能注册表并自动扫描
        self.skill_registry = SkillRegistry()
        self.skill_registry.auto_discover("skills")

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
        # all_tools = TOOLS_SCHEMA.copy()  # 本地工具
        # if self.mcp_adapter and self.mcp_adapter.tools_schema:
        #     all_tools.extend(self.mcp_adapter.tools_schema)
        all_tools = (
                self.skill_registry.get_all_tools() + 
                (self.mcp_adapter.tools_schema if self.mcp_adapter else [])
            )
        return all_tools
    


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

    async def run_stream(self, user_input: str) -> tuple[bool, str | Iterator[str]]:
        """
        返回: (是否需要流式, 结果)
        - 工具调用阶段：返回 (False, "执行中...")
        - 最终回答阶段：返回 (True, 文本迭代器)
        """
        # === 1. 记忆检索与构造 ===
        relevant_memories = self.memory.search_memories(self.session_id, user_input)
        #  构造带有“回忆”的 System Prompt
        memory_context = ""
        if relevant_memories:
            memory_str = "\n".join([f"- {m}" for m in relevant_memories])
            memory_context = f"\n【相关历史回忆】:\n{memory_str}\n请结合以上回忆回答用户问题。"
        # 注意：这里我们需要动态修改 System Prompt
        # 简单做法：在 context 的最前面插入一条 system 消息
        system_prompt = "你是一个有用的助手。"
        # ✅ 注入技能描述
        if self.skill_registry._skills:
            skills_desc = "\n".join([f"- {s.description}" for s in self.skill_registry._skills.values()])
            system_prompt += f"\n【可用技能】:\n{skills_desc}"
        # 注入记忆 (同 W5)
        if relevant_memories:
            system_prompt += memory_context
        # 确保 System Prompt 在历史最前面
        self.context_manager.set_system_message(system_prompt)
        # === 2. 确保 MCP 连接 ===
        await self._ensure_mcp_connected()

        # 输入用户上下文
        self.context_manager.add_message("user", user_input)
        # 设置最大迭代次数，防止模型陷入死循环（比如一直调用工具却不结束）
        max_iterations = 5
        for _ in range(max_iterations):
            messages = self.context_manager.get_messages()
            all_tools = self._merge_tool_schemas()
            
            # 一、 阻塞请求判断是否需要工具
            try:
                response_data = self.llm.chat_completion_with_tool_retry(messages, tools=all_tools)
            except Exception as e:
                return False, f"❌ 系统繁忙:: {str(e)}"
            
            # 1、解析工具调用
            tool_calls = self.parse_tool_calls(response_data)
             # 2、执行工具调用
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    args = tool_call["arguments"]
                    tool_id = tool_call["id"]
                    # 【关键】区分本地工具 vs MCP 工具
                    # ✅ 统一路由：优先查技能，再查 MCP，最后查本地
                    if "_" in tool_name and tool_name.split("_")[0] in self.skill_registry._skills:
                        result = self.skill_registry.dispatch(tool_name, args)
                        self.context_manager.add_tool_response(tool_id, tool_name, str(result))

                    elif tool_name.startswith("mcp_") and self.mcp_adapter:
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
            
            # 二、 最终回答阶段：返回流式迭代器
            return True, self.llm.chat_completion_stream(messages, tools=all_tools)
            
        return False, "️ 达到最大尝试次数"