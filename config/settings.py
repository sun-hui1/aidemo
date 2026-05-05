import os
from dotenv import load_dotenv

# 自动加载 .env 文件（如果存在）
load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

if not LLM_API_KEY:
    raise ValueError("❌ LLM_API_KEY 未配置，请在 .env 文件中设置。")