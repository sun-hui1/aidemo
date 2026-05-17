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
        "C:/Users/24534/Desktop"  # 允许访问的目录（请修改为你的路径）
    ]
}
async def main():
    agent = SimpleChatAgent( mcp_config=mcp_config)
    print("🤖 === 简易对话 Agent (输入 quit 退出) ===")
    
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
            response = await agent.run(user_input)
            print(f"🤖 Agent: {response}")
        except Exception as e:
            logger.error(f"运行异常: {e}\n{traceback.format_exc()}")
            print("🤖 Agent: 抱歉，处理请求时出现错误，请查看日志。")

if __name__ == "__main__":
    asyncio.run(main())