import requests
import json
import traceback
from config.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from utils.logger import get_logger
from utils.retry import robust_api_call
from typing import Iterator
logger = get_logger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = LLM_API_KEY
        self.base_url = LLM_BASE_URL.rstrip("/")
        self.model = LLM_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # 初始化历史消息列表
        self.conversation_history = []


    def chat_completion_with_tool_retry(self, messages: list, tools: list = None) -> dict:
        """
        发送消息并获取响应

        
        这是一个使用工具的聊天完成方法，可以向模型发送消息并获取响应。
        支持传入工具描述，让模型决定是否需要调用工具。
        :param messages: 消息列表，包含对话历史
        :param tools: 可选的工具描述列表，用于定义模型可以使用的工具
        :return: 包含 choice 的完整响应字典，包含模型返回的所有信息
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages
        }
        # 如果提供了工具，加入 payload
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        # 使用 json.dumps 显式序列化，确保中文等多语言字符正确处理
        json_payload = json.dumps(payload, ensure_ascii=False)
        logger.info(f"📤 发送到 LLM 的请求: {json_payload[:2000]}")
        try:
            return robust_api_call(self._send_request, url, payload)
        except Exception as e:
            logger.error(f"LLM 请求失败: {e}\n{traceback.format_exc()}")
            raise

    def _send_request(self, url, payload):
        """实际发送请求的私有方法"""
        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        if not response.ok:
            # 提取 DeepSeek 返回的具体错误信息
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            logger.error(f"🚫 API 返回 {response.status_code}:\n{json.dumps(error_body, ensure_ascii=False, indent=2)}")
            logger.error(f"📤 触发错误的 payload 摘要: model={payload.get('model')}, "
                         f"messages_count={len(payload.get('messages', []))}, "
                         f"tools_count={len(payload.get('tools', []))}")
        response.raise_for_status()
        return response.json()

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        logger.info("对话历史已清空")

    def chat_completion_stream(self, messages: list, tools: list = None) -> Iterator[str]:
        """流式对话：逐块 yield 模型生成的文本"""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True  # ✅ 开启流式
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            with requests.post(url, json=payload, headers=self.headers, stream=True, timeout=60) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8').strip()
                        if decoded.startswith("data: "):
                            data_str = decoded[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content  # ✅ 实时产出文本块
                            except json.JSONDecodeError:
                                continue
        except requests.exceptions.RequestException as e:
            logger.error(f"🔥 流式请求失败: {e}")
            raise RuntimeError("流式输出中断")