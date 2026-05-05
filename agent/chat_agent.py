from core.llm_client import LLMClient
from utils.logger import get_logger
from .context_manager import ContextManager  # 同级模块
from .tools import TOOLS_SCHEMA, AVAILABLE_FUNCTIONS
import json

logger = get_logger(__name__)

class SimpleChatAgent:
    def __init__(self):

        """
        初始化方法
        初始化LLM客户端实例
        """
        self.llm = LLMClient()  # 创建LLMClient类的实例并赋值给self.llm属性
        self.context_manager = ContextManager(max_tokens=40,model="gpt-4")
    def run(self, user_input: str) -> str:
        logger.info(f"📥 接收用户输入: {user_input}")
        # 当前阶段：直接转发给模型并返回结果
        response = self.llm.chat_completion(user_input)
        logger.info(f"📤 模型返回: {response[:50]}...")
        return response
    
    def run_with_context_manager(self, user_input: str) -> str:
        logger.info(f"📥 接收用户输入: {user_input}")
        # 多轮对话：通过上下文管理器来进行对话历史管理
        self.context_manager.add_message("user",user_input)
        message = self.context_manager.get_messages()
        response = self.llm.chat_completion_with_context_manager(message)
        self.context_manager.add_message("assistant",response)
        logger.info(f"📤 模型返回: {response[:50]}...")
        return response
    
    # 只是通过简单的在底层使用数组进行多轮对话
    # def runmulti(self, user_input: str) -> str:
    #     logger.info(f"📥 接收用户输入: {user_input}")
    #     # 当前阶段：直接转发给模型并返回结果
    #     response = self.llm.chat_completion_multi_turns(user_input)
    #     logger.info(f"📤 模型返回: {response[:50]}...")
    #     return response

    # 支持工具调用
    def run_with_tool(self, user_input: str) -> str:
        logger.info(f"📥 接收用户输入: {user_input}")
        # 1、输入用户上下文
        self.context_manager.add_message("user",user_input)
        # 2、开始循环
        while True:
            message = self.context_manager.get_messages()
            # 3、调用模型传入工具定义
            logger.info("开始调用模型")
            response_data = self.llm.chat_completion_with_tool(message, tools=TOOLS_SCHEMA)
            # 4、解析工具调用
            tool_calls = self.parse_tool_calls(response_data)
            # 5、执行工具调用
            if tool_calls:    
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    args = tool_call["arguments"]
                    tool_id = tool_call["id"]
                    # 执行本地函数
                    if tool_name in AVAILABLE_FUNCTIONS:
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
                return assistant_message
            
    # 支持并行工具调用与重试        
    def run_with_tool_retry(self, user_input: str) -> str:
        logger.info(f"📥 接收用户输入: {user_input}")
        # 1、输入用户上下文
        self.context_manager.add_message("user",user_input)
        # 设置最大迭代次数，防止模型陷入死循环（比如一直调用工具却不结束）
        max_iterations = 5
        iteration = 0

        # 2、开始循环
        while iteration < max_iterations:
            iteration += 1
            message = self.context_manager.get_messages()
            # 3、调用模型传入工具定义
            logger.info("开始调用模型")
            try:
                response_data = self.llm.chat_completion_with_tool_retry(message, tools=TOOLS_SCHEMA)
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
                    # 执行本地函数
                    if tool_name in AVAILABLE_FUNCTIONS:
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
            self.context_manager.add_assistant_message_with_tool_calls(message)
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

    