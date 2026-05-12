import requests
import json
import traceback
from config.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from utils.logger import get_logger
from utils.retry import robust_api_call
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

    def chat_completion(self, user_message: str) -> str:
        """单轮对话方法（保持原有功能不变）"""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": user_message}]
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            logger.info(f"LLM Response: {data}")
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            logger.error("⏳ LLM 请求超时")
            raise RuntimeError("模型响应超时，请检查网络或重试。")
        except requests.exceptions.HTTPError as e:
            logger.error(f"🔥 HTTP 错误: {e.response.text}")
            raise RuntimeError(f"API 调用失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"❌ 未知异常: {e}")
            raise

    def chat_completion_with_context_manager(self, user_message: list[dict]) -> str:
        """单轮对话方法（保持原有功能不变）"""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": user_message
        }
        logger.info(f"📥 通过context_manager接收用户输入: {user_message}")

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            # logger.info(f"LLM Response: {data}")
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            logger.error("⏳ LLM 请求超时")
            raise RuntimeError("模型响应超时，请检查网络或重试。")
        except requests.exceptions.HTTPError as e:
            logger.error(f"🔥 HTTP 错误: {e.response.text}")
            raise RuntimeError(f"API 调用失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"❌ 未知异常: {e}")
            raise
    def chat_completion_multi_turns(self, user_message: str) -> str:
        """多轮对话方法"""
        # 将用户消息添加到历史记录
        self.conversation_history.append({"role": "user", "content": user_message})
        
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": self.conversation_history  # 使用历史消息
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            logger.info(f"LLM Response: {data}")
            
            # 获取助手回复
            assistant_message = data["choices"][0]["message"]["content"]
            
            # 将助手回复也添加到历史记录
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
        except requests.exceptions.Timeout:
            logger.error("⏳ LLM 请求超时")
            raise RuntimeError("模型响应超时，请检查网络或重试。")
        except requests.exceptions.HTTPError as e:
            logger.error(f"🔥 HTTP 错误: {e.response.text}")
            raise RuntimeError(f"API 调用失败: {e.response.status号}")
        except Exception as e:
            logger.error(f"❌ 未知异常: {e}")
            raise

    # 支持工具调用
    def chat_completion_with_tool(self, messages: list, tools: list = None) -> dict:
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
        logger.info(f"📥 接收用户输入: {messages}")
        # 如果提供了工具，加入 payload
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        # 使用 json.dumps 显式序列化，确保中文等多语言字符正确处理
        json_payload = json.dumps(payload, ensure_ascii=False)
        logger.info(f"发送到 LLM 的请求: {json_payload}")
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"LLM 请求失败: {e}\n{traceback.format_exc()}")
            raise

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
        logger.info(f"发送到 LLM 的请求: {json_payload}")
        try:
            return robust_api_call(self._send_request, url, payload)
        except Exception as e:
            logger.error(f"LLM 请求失败: {e}\n{traceback.format_exc()}")
            raise

    def _send_request(self, url, payload):
        """实际发送请求的私有方法"""
        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        logger.info("对话历史已清空")
