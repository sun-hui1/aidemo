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

    def _normalize_schema(self, schema: dict) -> dict:
        """
        将 MCP 的 JSON Schema 规范化为 OpenAI function calling 兼容格式。
        确保顶层有 type: object，并递归清理不兼容字段。
        """
        if not isinstance(schema, dict):
            return {"type": "object", "properties": {}}

        normalized = {"type": "object"}

        # 复制 properties（如果存在且为 dict）
        props = schema.get("properties")
        if isinstance(props, dict):
            cleaned = {}
            for key, val in props.items():
                if isinstance(val, dict):
                    cleaned[key] = self._clean_property(val)
            normalized["properties"] = cleaned
        else:
            normalized["properties"] = {}

        # 复制 required（如果存在且为 list）
        required = schema.get("required")
        if isinstance(required, list):
            normalized["required"] = required

        return normalized

    def _clean_property(self, prop: dict) -> dict:
        """递归清理单个 property 定义，移除 DeepSeek 不支持的 JSON Schema 字段"""
        # 保留白名单字段
        allowed = {"type", "description", "properties", "required",
                   "items", "enum", "default", "minimum", "maximum",
                   "minLength", "maxLength", "pattern"}
        cleaned = {k: v for k, v in prop.items() if k in allowed}

        # 递归清理嵌套 properties
        if "properties" in cleaned and isinstance(cleaned["properties"], dict):
            cleaned["properties"] = {
                k: self._clean_property(v) if isinstance(v, dict) else v
                for k, v in cleaned["properties"].items()
            }
        # 递归清理嵌套 items（数组元素 schema）
        if "items" in cleaned and isinstance(cleaned["items"], dict):
            cleaned["items"] = self._clean_property(cleaned["items"])
        return cleaned

    async def _load_tools_schema(self) -> list[dict]:
        """将 MCP 工具转换为 OpenAI 兼容格式"""
        raw_tools = await self.client.list_tools()
        converted = []
        for tool in raw_tools:
            converted.append({
                "type": "function",
                "function": {
                    "name": f"mcp_{tool['name']}",  # 加前缀避免与本地工具冲突
                    "description": tool.get("description", ""),
                    "parameters": self._normalize_schema(tool.get("input_schema", {}))
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