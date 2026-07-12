# skills/file_skill.py
from skills.base_skill import BaseSkill, SkillResult
from typing import List, Dict, Any
import os
from pathlib import Path

class SecurityError(Exception):
    """安全异常"""
    pass

class FileSkill(BaseSkill):
    """文件操作技能"""
    
    @property
    def name(self) -> str:
        return "file"
    
    @property
    def description(self) -> str:
        return "提供文件读写、删除、列表和搜索功能。支持安全路径校验，只能访问工作区目录。"
    
    def get_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "file_read",
                    "description": "读取指定文件的内容，支持指定行号范围",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件路径（相对或绝对）"
                            },
                            "start_line": {
                                "type": "integer",
                                "description": "起始行号（从 1 开始），不指定则读取全部",
                                "default": None
                            },
                            "end_line": {
                                "type": "integer",
                                "description": "结束行号（包含），不指定则读到文件末尾",
                                "default": None
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "file_write",
                    "description": "写入内容到文件（会覆盖原内容），如果目录不存在会自动创建",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "content": {
                                "type": "string",
                                "description": "要写入的内容"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "file_append",
                    "description": "追加内容到文件末尾",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "content": {
                                "type": "string",
                                "description": "要追加的内容"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "file_delete",
                    "description": "删除指定文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件路径"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "file_list",
                    "description": "列出目录下的文件和子目录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dir_path": {
                                "type": "string",
                                "description": "目录路径"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "是否递归列出",
                                "default": False
                            },
                            "pattern": {
                                "type": "string",
                                "description": "文件名匹配模式（如 *.py）",
                                "default": None
                            }
                        },
                        "required": ["dir_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "file_search",
                    "description": "在目录中搜索文件内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "搜索模式（正则表达式）"
                            },
                            "dir_path": {
                                "type": "string",
                                "description": "搜索的目录路径",
                                "default": "."
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "文件名匹配模式（如 *.py）",
                                "default": "*"
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            }
        ]
    
    def execute(self, tool_name: str, arguments: Dict) -> Any:
        """执行具体的文件操作"""
        if tool_name == "read":
            return self._read_file(
                arguments["path"],
                arguments.get("start_line"),
                arguments.get("end_line")
            )
        elif tool_name == "write":
            return self._write_file(arguments["path"], arguments["content"])
        elif tool_name == "append":
            return self._append_file(arguments["path"], arguments["content"])
        elif tool_name == "delete":
            return self._delete_file(arguments["path"])
        elif tool_name == "list":
            return self._list_directory(
                arguments["dir_path"],
                arguments.get("recursive", False),
                arguments.get("pattern")
            )
        elif tool_name == "search":
            return self._search_in_files(
                arguments["pattern"],
                arguments.get("dir_path", "."),
                arguments.get("file_pattern", "*")
            )
        raise ValueError(f"未知工具：{tool_name}")
    
    def _read_file(self, path: str, start_line: int = None, end_line: int = None) -> str:
        """安全读取文件"""
        safe_path = self._validate_path(path)
        
        if not safe_path.exists():
            return f"❌ 文件不存在：{safe_path}"
        
        try:
            with open(safe_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 如果指定了行号范围，进行切片
            if start_line is not None or end_line is not None:
                # 转换为 0-based 索引
                start_idx = (start_line - 1) if start_line else 0
                end_idx = end_line if end_line else len(lines)
                lines = lines[start_idx:end_idx]
            
            content = ''.join(lines)
            return f"📄 {safe_path}\n\n{content}"
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(safe_path, 'r', encoding='gbk') as f:
                    content = f.read()
                return f"📄 {safe_path} (GBK 编码)\n\n{content}"
            except Exception as e:
                return f"读取失败（二进制文件？）: {str(e)}"
        except Exception as e:
            return f"读取失败：{str(e)}"
    
    def _write_file(self, path: str, content: str) -> str:
        """安全写入文件"""
        safe_path = self._validate_path(path)
        
        try:
            # 确保目录存在
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 检查文件是否已存在（避免意外覆盖）
            if safe_path.exists():
                backup_msg = f"（已存在的文件将被覆盖）"
            else:
                backup_msg = ""
            
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            line_count = len(content.splitlines())
            char_count = len(content)
            return f"✅ 成功写入文件：{safe_path} {backup_msg}\n   行数：{line_count}, 字符数：{char_count}"
        except Exception as e:
            return f"写入失败：{str(e)}"
    
    def _append_file(self, path: str, content: str) -> str:
        """安全追加文件"""
        safe_path = self._validate_path(path)
        
        if not safe_path.exists():
            return f"❌ 文件不存在：{safe_path}（请先使用 file_write 创建）"
        
        try:
            with open(safe_path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            return f"✅ 成功追加内容到：{safe_path}"
        except Exception as e:
            return f"追加失败：{str(e)}"
    
    def _delete_file(self, path: str) -> str:
        """安全删除文件"""
        safe_path = self._validate_path(path)
        
        if not safe_path.exists():
            return f"⚠️ 文件不存在：{safe_path}"
        
        try:
            safe_path.unlink()
            return f"✅ 已删除文件：{safe_path}"
        except Exception as e:
            return f"删除失败：{str(e)}"
    
    def _list_directory(self, dir_path: str, recursive: bool = False, pattern: str = None) -> str:
        """列出目录内容"""
        safe_path = self._validate_path(dir_path, is_dir=True)
        
        if not safe_path.exists():
            return f"❌ 目录不存在：{safe_path}"
        
        try:
            if recursive:
                files = []
                for root, dirs, filenames in os.walk(safe_path):
                    # 过滤忽略的目录
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
                    
                    level = root.replace(str(safe_path), '').count(os.sep)
                    indent = ' ' * 2 * level
                    files.append(f"{indent}{os.path.basename(root)}/")
                    
                    sub_indent = ' ' * 2 * (level + 1)
                    for filename in sorted(filenames):
                        if pattern is None or self._match_pattern(filename, pattern):
                            files.append(f"{sub_indent}{filename}")
                
                return "\n".join(files)
            else:
                items = []
                for item in sorted(safe_path.iterdir()):
                    if item.name.startswith('.') or item.name in ['__pycache__', 'node_modules']:
                        continue
                    if pattern is None or self._match_pattern(item.name, pattern):
                        suffix = "/" if item.is_dir() else ""
                        items.append(f"{item.name}{suffix}")
                
                return "\n".join(items)
        except Exception as e:
            return f"列出失败：{str(e)}"
    
    def _search_in_files(self, pattern: str, dir_path: str = ".", file_pattern: str = "*") -> str:
        """在文件中搜索内容"""
        import re
        
        safe_path = self._validate_path(dir_path, is_dir=True)
        
        try:
            regex = re.compile(pattern)
            results = []
            
            for file in safe_path.rglob(file_pattern):
                if not file.is_file():
                    continue
                
                # 跳过二进制文件和隐藏文件
                if file.name.startswith('.'):
                    continue
                
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                results.append(f"{file}:{line_num}: {line.strip()}")
                except (UnicodeDecodeError, PermissionError):
                    continue
            
            if not results:
                return f"🔍 未找到匹配 '{pattern}' 的内容"
            
            return f"🔍 找到 {len(results)} 个匹配:\n\n" + "\n".join(results[:50])  # 限制显示数量
        except Exception as e:
            return f"搜索失败：{str(e)}"
    
    def _validate_path(self, path: str, is_dir: bool = False) -> Path:
        """路径安全校验，防止目录遍历攻击"""
        allowed_base = Path("/workspace").resolve()
        
        # 解析路径
        if Path(path).is_absolute():
            target = Path(path).resolve()
        else:
            target = (Path.cwd() / path).resolve()
        
        # 安全检查
        if not str(target).startswith(str(allowed_base)):
            raise SecurityError(f"🚫 禁止访问工作区外的路径：{path}\n   允许的路径：{allowed_base}")
        
        # 如果是目录且不存在，创建它
        if is_dir and not target.exists():
            target.mkdir(parents=True, exist_ok=True)
        
        return target
    
    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """简单的通配符匹配"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def call(self, tool_name: str, **kwargs) -> SkillResult:
        """执行具体的文件操作"""
        try:
            if tool_name == "read":
                result = self._read_file(
                    kwargs.get("path"),
                    kwargs.get("start_line"),
                    kwargs.get("end_line")
                )
            elif tool_name == "write":
                result = self._write_file(kwargs.get("path"), kwargs.get("content"))
            elif tool_name == "append":
                result = self._append_file(kwargs.get("path"), kwargs.get("content"))
            elif tool_name == "delete":
                result = self._delete_file(kwargs.get("path"))
            elif tool_name == "list":
                result = self._list_directory(
                    kwargs.get("dir_path"),
                    kwargs.get("recursive", False),
                    kwargs.get("pattern")
                )
            elif tool_name == "search":
                result = self._search_in_files(
                    kwargs.get("pattern"),
                    kwargs.get("dir_path", "."),
                    kwargs.get("file_pattern", "*")
                )
            else:
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"未知工具：{tool_name}",
                    message=f"{self.name} 技能不包含此工具"
                )
            
            return SkillResult(
                success=True,
                data=result,
                error=None,
                message="操作完成"
            )
        except SecurityError as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="安全校验失败"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="操作执行过程中发生错误"
            )


# 自动注册
if __name__ == "__main__":
    from core.skill_registry import SkillRegistry
    registry = SkillRegistry()
    registry.register(FileSkill)
