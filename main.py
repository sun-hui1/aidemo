import traceback
from agent.chat_agent import SimpleChatAgent
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    agent = SimpleChatAgent()
    print("🤖 === 简易对话 Agent (输入 quit 退出) ===")
    
    while True:
        user_input = input("\n👤 你: ").strip()
        if user_input.lower() in {"quit", "exit", "q"}:
            print("👋 再见！")
            break
        if not user_input:
            continue
            
        try:
            # response = agent.runmulti(user_input)
            response = agent.run_with_tool_retry(user_input)
            print(f"🤖 Agent: {response}")
        except Exception as e:
            logger.error(f"运行异常: {e}\n{traceback.format_exc()}")
            print("🤖 Agent: 抱歉，处理请求时出现错误，请查看日志。")

if __name__ == "__main__":
    main()