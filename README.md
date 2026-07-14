# AI 开发编码助手 (AI Coding Assistant)

#### 项目介绍
基于 LLM 的智能代码助手，提供代码分析、生成、审查、重构等核心能力，支持 MCP 协议扩展。

#### 软件架构
```
a_my_agent/
├── config/          # 配置层：环境配置、系统设置
├── core/            # 核心基础设施：LLM 客户端、记忆存储、技能注册表
├── agent/           # 对话管理层：聊天 Agent、上下文管理、工具适配
├── engines/         # 业务逻辑层：代码引擎、项目引擎、规划引擎
├── skills/          # 工具操作层：封装引擎能力为 LLM 可调用的工具
├── utils/           # 工具层：日志、重试、数据库等通用工具
└── main.py          # 程序入口
```

**核心设计理念：**
- **Engine（引擎）**：专注业务逻辑实现（如代码分析、生成、审查的具体算法）
- **Skill（技能）**：作为适配层，将 Engine 能力转换为 LLM 可理解的工具格式
- **Agent（代理）**：负责对话管理、工具调度、上下文维护

#### 已实现功能
1. **代码技能 (code)**：6 个工具
   - code_analyze: 代码结构分析
   - code_generate: 代码生成
   - code_review: 代码质量审查
   - code_explain: 代码解释
   - code_refactor: 代码重构
   - code_modify: 代码修改

2. **文件技能 (file)**：6 个工具
   - file_read/write/append/delete/list/search

3. **代码执行技能 (code_exec)**：2 个工具
   - execute_python: 安全 Python 代码执行
   - execute_shell: Shell 命令执行

4. **天气技能 (weather)**：1 个工具
   - weather_get_current: 天气查询

5. **MCP 协议支持**：可连接外部 MCP Server 扩展能力

#### 安装教程
1. 克隆项目：`git clone <repo_url>`
2. 安装依赖：`pip install -r requirements.txt`
3. 配置环境变量：复制 `.env.example` 到 `.env` 并填写 API Key

#### 使用说明
```bash
python main.py
```
然后输入自然语言指令，例如：
- "分析当前目录下的 main.py 文件"
- "生成一个计算斐波那契数列的 Python 函数"
- "审查 skills/code_skill.py 的代码质量"

#### 参与贡献
1. Fork 本仓库
2. 新建 Feat_xxx 分支
3. 提交代码
4. 新建 Pull Request
