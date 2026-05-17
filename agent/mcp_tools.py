# agent/mcp_tools.py
import asyncio
from core.mcp_client import MCPClient
from utils.logger import get_logger

logger = get_logger(__name__)

class MCPToolAdapter:
    """将 MCP 工具适配为本地工具格式"""
    
    def __init__(self, server_command: str, server_args: list[str] = None):
        self.server_command = server_command
        self.server_args = server_args or []
        self.client: MCPClient | None = None
        self.tools_schema: list[dict] = []  # 适配后的工具描述

    async def connect(self):
        """建立 MCP 连接并加载工具"""
        self.client = MCPClient(self.server_command, self.server_args)
        await self.client.__aenter__()
        self.tools_schema = await self._load_tools_schema()
        logger.info(f"✅ 已加载 {len(self.tools_schema)} 个 MCP 工具")

    async def disconnect(self):
        """关闭 MCP 连接"""
        if self.client:
            await self.client.__aexit__(None, None, None)

    async def _load_tools_schema(self) -> list[dict]:
        """将 MCP 工具转换为 OpenAI 兼容格式"""
        raw_tools = await self.client.list_tools()
        converted = []
        for tool in raw_tools:
            converted.append({
                "type": "function",
                "function": {
                    "name": f"mcp_{tool['name']}",  # 加前缀避免与本地工具冲突
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })
        return converted

    async def execute(self, tool_name: str, arguments: dict) -> str:
        """执行 MCP 工具（去掉 mcp_ 前缀）"""
        if not self.client:
            return "错误：MCP 未连接"
        
        real_name = tool_name.replace("mcp_", "", 1)
        try:
            result = await self.client.call_tool(real_name, arguments)
            logger.info(f"✅ MCP 工具 {real_name} 执行成功")
            return result
        except Exception as e:
            logger.error(f"❌ MCP 工具 {real_name} 执行失败: {e}")
            return f"MCP 执行错误: {str(e)}"