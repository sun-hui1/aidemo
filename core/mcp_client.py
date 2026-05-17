# core/mcp_client.py
import asyncio
import json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from utils.logger import get_logger

logger = get_logger(__name__)

class MCPClient:
    def __init__(self, server_command: str, server_args: list[str] = None):
        """
        初始化 MCP 客户端
        :param server_command: MCP Server 的启动命令（如 'npx', 'python'）
        :param server_args: Server 的参数列表（如 ['-y', '@modelcontextprotocol/server-filesystem', '/tmp']）
        """
        self.server_params = StdioServerParameters(
            command=server_command,
            args=server_args or [],
        )
        self.exit_stack = AsyncExitStack()
        self.session: ClientSession | None = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 启动 Server 进程并建立连接
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(self.server_params)
        )
        read, write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self.session.initialize()
        logger.info(f"🔗 MCP 连接已建立: {self.server_params.command}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.exit_stack.aclose()
        logger.info("🔌 MCP 连接已关闭")

    async def list_tools(self) -> list[dict]:
        """获取 Server 提供的所有工具"""
        response = await self.session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema  # JSON Schema 格式
            }
            for tool in response.tools
        ]

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """调用指定工具"""
        response = await self.session.call_tool(name=tool_name, arguments=arguments)
        # 解析返回结果（MCP 返回的是 Content 列表）
        results = []
        for content in response.content:
            if content.type == "text":
                results.append(content.text)
            elif content.type == "image":
                results.append(f"[图片: {content.mimeType}]")
            elif content.type == "resource":
                results.append(f"[资源: {content.resource.uri}]")
        return "\n".join(results)

    async def list_resources(self) -> list[dict]:
        """获取 Server 提供的所有资源"""
        response = await self.session.list_resources()
        return [
            {
                "uri": res.uri,
                "name": res.name,
                "description": res.description,
                "mime_type": res.mimeType
            }
            for res in response.resources
        ]

    async def read_resource(self, uri: str) -> str:
        """读取指定资源内容"""
        response = await self.session.read_resource(uri=uri)
        return response.contents[0].text if response.contents else ""