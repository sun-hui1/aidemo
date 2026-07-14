"""
代码执行沙箱技能
提供安全的 Python 代码执行和 Shell 命令执行能力
"""
import subprocess
import sys
import io
import os
import tempfile
import json
from typing import Dict, Any, Optional, List
from contextlib import redirect_stdout, redirect_stderr
from skills.base_skill import BaseSkill, SkillResult


class CodeExecSkill(BaseSkill):
    """代码执行沙箱技能"""
    
    def __init__(self):
        super().__init__(
            name="code_exec",
            description="安全地执行 Python 代码片段或 Shell 命令",
            version="1.0.0"
        )
        self.allowed_modules = {
            'math', 'random', 'datetime', 'collections', 'itertools',
            'functools', 're', 'json', 'csv', 'hashlib', 'base64',
            'string', 'textwrap', 'unicodedata', 'typing'
        }
        self.work_dir = os.getcwd()

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_python",
                    "description": "在隔离环境中执行 Python 代码片段。适用于数据处理、算法验证、脚本生成等。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "要执行的 Python 代码字符串"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "执行超时时间（秒），默认 30 秒",
                                "default": 30
                            }
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_shell",
                    "description": "执行 Shell 命令。适用于文件操作、系统信息查询、调用外部工具等。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "要执行的 Shell 命令"
                            },
                            "cwd": {
                                "type": "string",
                                "description": "命令执行的工作目录，默认为当前工作区",
                                "default": None
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "执行超时时间（秒），默认 60 秒",
                                "default": 60
                            }
                        },
                        "required": ["command"]
                    }
                }
            }
        ]

    def execute_python(self, code: str, timeout: int = 30) -> SkillResult:
        """
        执行 Python 代码
        注意：这是一个基础沙箱，生产环境建议使用 Docker 或 gVisor 进行更强隔离
        """
        try:
            # 基础安全检查
            dangerous_patterns = ['__import__', 'eval(', 'exec(', 'open(', 
                                  'subprocess', 'os.system', 'os.popen']
            for pattern in dangerous_patterns:
                if pattern in code:
                    # 允许必要的 import，但限制危险调用
                    if pattern == '__import__' and 'import ' in code:
                        continue 
                    if pattern in ['open(', 'os.system', 'os.popen', 'subprocess']:
                        return SkillResult(
                            success=False,
                            data=None,
                            error=f"检测到潜在危险操作: {pattern}. 出于安全考虑，此操作被禁止。",
                            message="代码包含受限的系统调用。请尝试使用提供的工具函数而非直接系统调用。"
                        )

            # 创建临时文件执行
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # 包装代码以捕获输出
                safe_code_lines = [
                    "import sys",
                    "import json",
                    "from io import StringIO",
                    "",
                    "# 重定向输出",
                    "old_stdout = sys.stdout",
                    "old_stderr = sys.stderr",
                    "sys.stdout = StringIO()",
                    "sys.stderr = StringIO()",
                    "",
                    "try:"
                ]
                
                for line in code.splitlines():
                    safe_code_lines.append("    " + line)
                
                safe_code_lines.extend([
                    '    result = {"success": True, "stdout": sys.stdout.getvalue(), "stderr": sys.stderr.getvalue()}',
                    "except Exception as e:",
                    '    result = {"success": False, "stdout": sys.stdout.getvalue(), "stderr": str(e), "error_type": type(e).__name__}',
                    "finally:",
                    "    sys.stdout = old_stdout",
                    "    sys.stderr = old_stderr",
                    "    print(json.dumps(result))"
                ])
                
                safe_code = "\n".join(safe_code_lines)
                f.write(safe_code)
                temp_file = f.name

            try:
                # 执行临时文件
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.work_dir
                )
                
                if result.returncode != 0:
                    return SkillResult(
                        success=False,
                        data=None,
                        error=f"执行失败: {result.stderr}",
                        message="Python 代码执行出错"
                    )
                
                # 解析 JSON 结果
                try:
                    output = json.loads(result.stdout.strip())
                    return SkillResult(
                        success=output.get('success', False),
                        data={
                            "stdout": output.get('stdout', ''),
                            "stderr": output.get('stderr', '')
                        },
                        error=output.get('error_type') if not output.get('success') else None,
                        message="代码执行完成"
                    )
                except json.JSONDecodeError:
                    return SkillResult(
                        success=False,
                        data=None,
                        error="无法解析执行结果",
                        message=result.stdout
                    )
                    
            finally:
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return SkillResult(
                success=False,
                data=None,
                error=f"代码执行超时（>{timeout}秒）",
                message="执行时间过长，已终止"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="执行过程中发生未知错误"
            )

    def execute_shell(self, command: str, cwd: Optional[str] = None, timeout: int = 60) -> SkillResult:
        """
        执行 Shell 命令
        """
        try:
            # 安全检查：禁止某些危险命令
            dangerous_commands = ['rm -rf /', 'mkfs', 'dd if=', ':(){:|:&};:', 'chmod -R 777 /']
            for dangerous in dangerous_commands:
                if dangerous in command:
                    return SkillResult(
                        success=False,
                        data=None,
                        error=f"检测到危险命令: {dangerous}",
                        message="该命令可能对系统造成严重损害，已被拦截"
                    )

            work_dir = cwd if cwd else self.work_dir
            
            # 确保工作目录存在且在工作区内
            if not os.path.exists(work_dir):
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"工作目录不存在: {work_dir}",
                    message="请检查路径是否正确"
                )
            
            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir,
                env=os.environ.copy()
            )
            
            return SkillResult(
                success=(result.returncode == 0),
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                },
                error=None if result.returncode == 0 else f"命令返回非零退出码: {result.returncode}",
                message=f"命令执行完成 (退出码: {result.returncode})"
            )
            
        except subprocess.TimeoutExpired:
            return SkillResult(
                success=False,
                data=None,
                error=f"命令执行超时（>{timeout}秒）",
                message="执行时间过长，已终止"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="Shell 执行过程中发生未知错误"
            )

    def call(self, tool_name: str, **kwargs) -> SkillResult:
        if tool_name == "execute_python":
            return self.execute_python(
                code=kwargs.get("code", ""),
                timeout=kwargs.get("timeout", 30)
            )
        elif tool_name == "execute_shell":
            return self.execute_shell(
                command=kwargs.get("command", ""),
                cwd=kwargs.get("cwd"),
                timeout=kwargs.get("timeout", 60)
            )
        else:
            return SkillResult(
                success=False,
                data=None,
                error=f"未知工具: {tool_name}",
                message=f"{self.name} 技能不包含此工具"
            )
