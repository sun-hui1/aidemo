from dotenv import load_dotenv
import asyncio
load_dotenv()

import traceback
from agent.chat_agent import SimpleChatAgent
from utils.logger import get_logger

logger = get_logger(__name__)
mcp_config = {
    "command": "npx",  # Node.js 的包执行器
    "args": [
        "-y",  # 自动确认安装
        "@modelcontextprotocol/server-filesystem",  # 官方文件系统 Server
        "C:/Users/24534/Desktop/AiPJ/a_my_agent/AgentLearning"  # 允许访问的目录（请修改为你的路径）
    ]
}
async def main():
    agent = SimpleChatAgent( mcp_config=mcp_config)
    print("🤖 === 简易对话 Agent (输入 quit 退出) ===")
    try:
        while True:
            try:
                # ✅ 使用 to_thread 避免 input() 阻塞异步事件循环
                user_input = await asyncio.to_thread(input, "\n 你: ")
            except EOFError:
                break
            if user_input.lower() in {"quit", "exit", "q"}:
                print("👋 再见！")
                break
            if not user_input:
                continue
                
            try:
                # response = agent.runmulti(user_input)
                is_stream, result = await agent.run_stream(user_input)
                print("🤖 Agent: ", end="", flush=True)
                if is_stream:
                    # ✅ 实时打印流式块
                    for chunk in result:
                        print(chunk, end="", flush=True)
                    print()  # 换行
                else:
                    print(result)
            except Exception as e:
                logger.error(f"运行异常: {e}\n{traceback.format_exc()}")
                print("🤖 Agent: 抱歉，处理请求时出现错误，请查看日志。")
    finally:
        if agent.mcp_adapter:
            await agent.mcp_adapter.disconnect()

if __name__ == "__main__":
    asyncio.run(main())