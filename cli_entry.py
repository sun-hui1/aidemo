#!/usr/bin/env python3
"""
AI 编码助手 - 交互式命令行入口

支持功能:
- 代码审查: review <文件路径>
- 代码分析: analyze <文件路径>
- 代码生成: generate <描述>
- 代码解释: explain <文件路径>
- 代码重构: refactor <文件路径>
- 文件操作: read/write/list 等
- 代码执行: exec <python 代码>
- 退出: exit/quit
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from skills.code_skill import CodeSkill
from skills.file_skill import FileSkill
from skills.code_exec_skill import CodeExecSkill

console = Console()

class CommandCompleter(Completer):
    """命令自动补全"""
    
    COMMANDS = [
        'review', 'analyze', 'generate', 'explain', 'refactor', 'modify',
        'read', 'write', 'append', 'delete', 'list', 'search',
        'exec', 'shell',
        'help', 'exit', 'quit', 'clear'
    ]
    
    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        if word.startswith('/'):
            for cmd in self.COMMANDS:
                if cmd.startswith(word[1:]):
                    yield Completion(f'/{cmd}', start_position=-len(word[1:]))


class AICodingAssistant:
    """AI 编码助手交互界面"""
    
    def __init__(self):
        self.code_skill = CodeSkill()
        self.file_skill = FileSkill()
        self.exec_skill = CodeExecSkill()
        
        # 初始化历史文件
        history_path = Path.home() / '.ai_coding_assistant_history'
        self.session = PromptSession(
            completer=CommandCompleter(),
            history=FileHistory(str(history_path)),
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            style=None  # 禁用自定义样式避免冲突
        )
        
        self._show_welcome()
    
    def _show_welcome(self):
        """显示欢迎信息"""
        welcome_text = """
# 🤖 AI 编码助手

## 可用命令

### 代码相关
- `/review <文件>` - 审查代码质量
- `/analyze <文件>` - 分析代码复杂度
- `/generate <描述>` - 生成代码
- `/explain <文件>` - 解释代码功能
- `/refactor <文件>` - 重构代码建议
- `/modify <文件> <修改说明>` - 修改代码

### 文件操作
- `/read <文件>` - 读取文件内容
- `/write <文件> <内容>` - 写入文件
- `/append <文件> <内容>` - 追加内容
- `/delete <文件>` - 删除文件
- `/list [目录]` - 列出文件
- `/search <关键词> [目录]` - 搜索文件

### 代码执行
- `/exec <Python 代码>` - 执行 Python 代码
- `/shell <命令>` - 执行 Shell 命令

### 其他
- `/help` - 显示帮助
- `/clear` - 清屏
- `/exit` 或 `/quit` - 退出

**示例**:
```
/review main.py
/generate 创建一个快速排序函数
/read src/utils.py
```
        """
        console.print(Panel(Markdown(welcome_text), title="🚀 欢迎使用", border_style="green"))
    
    def _parse_command(self, user_input: str):
        """解析用户输入的命令"""
        user_input = user_input.strip()
        
        # 支持 /command 和 command 两种格式
        if user_input.startswith('/'):
            user_input = user_input[1:]
        
        parts = user_input.split(maxsplit=1)
        if not parts:
            return None, None
        
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        return cmd, args
    
    def _handle_review(self, args: str):
        """处理代码审查"""
        if not args:
            console.print("[red]❌ 请指定文件路径：/review <文件路径>[/red]")
            return
        
        file_path = args.strip()
        if not Path(file_path).exists():
            console.print(f"[red]❌ 文件不存在：{file_path}[/red]")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            console.print(f"\n[bold blue]🔍 正在审查：{file_path}[/bold blue]\n")
            
            result = self.code_skill.call('code_review', {
                'code': code,
                'language': Path(file_path).suffix.lstrip('.') or 'python'
            })
            
            if isinstance(result, dict) and 'issues' in result:
                issues = result['issues']
                score = result.get('score', 0)
                
                # 显示评分
                if score >= 90:
                    color = "green"
                    emoji = "✅"
                elif score >= 70:
                    color = "yellow"
                    emoji = "⚠️"
                else:
                    color = "red"
                    emoji = "❌"
                
                console.print(Panel(f"代码质量评分：[bold {color}]{emoji} {score}/100[/bold {color}]", 
                                   border_style=color))
                
                # 显示问题
                if issues:
                    console.print(f"\n[bold]发现 {len(issues)} 个问题:[/bold]\n")
                    for i, issue in enumerate(issues, 1):
                        severity = issue.get('severity', 'info').upper()
                        severity_color = {
                            'ERROR': 'red',
                            'WARNING': 'yellow',
                            'INFO': 'blue'
                        }.get(severity, 'white')
                        
                        console.print(f"{i}. [{severity_color}]{severity}[/{severity_color}] - {issue.get('message', '')}")
                        if 'line' in issue:
                            console.print(f"   📍 行号：{issue['line']}")
                        if 'suggestion' in issue:
                            console.print(f"   💡 建议：{issue['suggestion']}")
                        console.print()
                else:
                    console.print("[green]✅ 未发现明显问题！[/green]")
            else:
                console.print(f"[gray]{result}[/gray]")
                
        except Exception as e:
            console.print(f"[red]❌ 审查失败：{str(e)}[/red]")
    
    def _handle_analyze(self, args: str):
        """处理代码分析"""
        if not args:
            console.print("[red]❌ 请指定文件路径：/analyze <文件路径>[/red]")
            return
        
        file_path = args.strip()
        if not Path(file_path).exists():
            console.print(f"[red]❌ 文件不存在：{file_path}[/red]")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            console.print(f"\n[bold blue]📊 正在分析：{file_path}[/bold blue]\n")
            
            result = self.code_skill.call('code_analyze', {
                'code': code,
                'language': Path(file_path).suffix.lstrip('.') or 'python'
            })
            
            if isinstance(result, dict):
                metrics = result.get('metrics', {})
                
                console.print("[bold]代码指标:[/bold]")
                console.print(f"  • 行数：{metrics.get('lines', 0)}")
                console.print(f"  • 字符数：{metrics.get('characters', 0)}")
                console.print(f"  • 函数数：{metrics.get('functions', 0)}")
                console.print(f"  • 类数：{metrics.get('classes', 0)}")
                console.print(f"  • 注释行数：{metrics.get('comment_lines', 0)}")
                console.print(f"  • 空行数：{metrics.get('blank_lines', 0)}")
                
                complexity = metrics.get('complexity', {})
                if complexity:
                    console.print(f"\n[bold]复杂度分析:[/bold]")
                    console.print(f"  • 圈复杂度：{complexity.get('cyclomatic', 'N/A')}")
                    console.print(f"  • 认知复杂度：{complexity.get('cognitive', 'N/A')}")
                
                smells = result.get('code_smells', [])
                if smells:
                    console.print(f"\n[bold yellow]⚠️ 代码异味 ({len(smells)}):[/bold yellow]")
                    for smell in smells[:5]:  # 只显示前 5 个
                        console.print(f"  • {smell.get('type', '')}: {smell.get('description', '')}")
                
                suggestions = result.get('suggestions', [])
                if suggestions:
                    console.print(f"\n[bold green]💡 改进建议:[/bold green]")
                    for sug in suggestions[:5]:  # 只显示前 5 个
                        console.print(f"  • {sug}")
            else:
                console.print(f"[gray]{result}[/gray]")
                
        except Exception as e:
            console.print(f"[red]❌ 分析失败：{str(e)}[/red]")
    
    def _handle_explain(self, args: str):
        """处理代码解释"""
        if not args:
            console.print("[red]❌ 请指定文件路径：/explain <文件路径>[/red]")
            return
        
        file_path = args.strip()
        if not Path(file_path).exists():
            console.print(f"[red]❌ 文件不存在：{file_path}[/red]")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            console.print(f"\n[bold blue]📖 正在解释：{file_path}[/bold blue]\n")
            
            result = self.code_skill.call('code_explain', {
                'code': code,
                'language': Path(file_path).suffix.lstrip('.') or 'python'
            })
            
            if isinstance(result, dict):
                summary = result.get('summary', '')
                if summary:
                    console.print(Panel(Markdown(summary), title="📝 代码摘要", border_style="cyan"))
                
                functions = result.get('functions', [])
                if functions:
                    console.print(f"\n[bold]主要函数:[/bold]")
                    for func in functions:
                        console.print(f"  • `{func.get('name', '')}`: {func.get('description', '')}")
            else:
                console.print(f"[gray]{result}[/gray]")
                
        except Exception as e:
            console.print(f"[red]❌ 解释失败：{str(e)}[/red]")
    
    def _handle_generate(self, args: str):
        """处理代码生成"""
        if not args:
            console.print("[red]❌ 请描述要生成的代码：/generate <描述>[/red]")
            return
        
        console.print(f"\n[bold blue]✨ 正在生成代码：{args}[/bold blue]\n")
        
        try:
            result = self.code_skill.call('code_generate', {
                'description': args,
                'language': 'python'
            })
            
            if isinstance(result, dict):
                code = result.get('code', '')
                if code:
                    console.print(Syntax(code, "python", line_numbers=True, theme="monokai"))
                    
                    explanation = result.get('explanation', '')
                    if explanation:
                        console.print(f"\n[bold]说明:[/bold] {explanation}")
            else:
                console.print(f"[gray]{result}[/gray]")
                
        except Exception as e:
            console.print(f"[red]❌ 生成失败：{str(e)}[/red]")
    
    def _handle_refactor(self, args: str):
        """处理代码重构"""
        if not args:
            console.print("[red]❌ 请指定文件路径：/refactor <文件路径>[/red]")
            return
        
        file_path = args.strip()
        if not Path(file_path).exists():
            console.print(f"[red]❌ 文件不存在：{file_path}[/red]")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            console.print(f"\n[bold blue]🔄 正在分析重构建议：{file_path}[/bold blue]\n")
            
            result = self.code_skill.call('code_refactor', {
                'code': code,
                'language': Path(file_path).suffix.lstrip('.') or 'python'
            })
            
            if isinstance(result, dict):
                suggestions = result.get('suggestions', [])
                if suggestions:
                    console.print(Panel(Markdown('\n'.join([f"{i+1}. {s}" for i, s in enumerate(suggestions)])), 
                                       title="💡 重构建议", border_style="magenta"))
                
                refactored_code = result.get('refactored_code', '')
                if refactored_code and refactored_code != code:
                    console.print("\n[bold]重构后的代码:[/bold]")
                    console.print(Syntax(refactored_code, "python", line_numbers=True, theme="monokai"))
            else:
                console.print(f"[gray]{result}[/gray]")
                
        except Exception as e:
            console.print(f"[red]❌ 重构失败：{str(e)}[/red]")
    
    def _handle_file_command(self, cmd: str, args: str):
        """处理文件操作命令"""
        file_commands = {
            'read': self._file_read,
            'write': self._file_write,
            'append': self._file_append,
            'delete': self._file_delete,
            'list': self._file_list,
            'search': self._file_search
        }
        
        if cmd in file_commands:
            file_commands[cmd](args)
        else:
            console.print(f"[red]❌ 未知命令：{cmd}[/red]")
    
    def _file_read(self, args: str):
        """读取文件"""
        if not args:
            console.print("[red]❌ 请指定文件路径：/read <文件路径>[/red]")
            return
        
        file_path = args.strip()
        try:
            result = self.file_skill.call('file_read', {'file_path': file_path})
            if isinstance(result, dict) and 'content' in result:
                content = result['content']
                ext = Path(file_path).suffix.lstrip('.') or 'text'
                console.print(Syntax(content, ext, line_numbers=True, theme="monokai"))
            else:
                console.print(f"[gray]{result}[/gray]")
        except Exception as e:
            console.print(f"[red]❌ 读取失败：{str(e)}[/red]")
    
    def _file_write(self, args: str):
        """写入文件"""
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            console.print("[red]❌ 用法：/write <文件路径> <内容>[/red]")
            return
        
        file_path, content = parts[0], parts[1]
        try:
            result = self.file_skill.call('file_write', {
                'file_path': file_path,
                'content': content,
                'overwrite': True
            })
            console.print(f"[green]✅ 文件已写入：{file_path}[/green]")
        except Exception as e:
            console.print(f"[red]❌ 写入失败：{str(e)}[/red]")
    
    def _file_append(self, args: str):
        """追加内容"""
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            console.print("[red]❌ 用法：/append <文件路径> <内容>[/red]")
            return
        
        file_path, content = parts[0], parts[1]
        try:
            result = self.file_skill.call('file_append', {
                'file_path': file_path,
                'content': content
            })
            console.print(f"[green]✅ 内容已追加：{file_path}[/green]")
        except Exception as e:
            console.print(f"[red]❌ 追加失败：{str(e)}[/red]")
    
    def _file_delete(self, args: str):
        """删除文件"""
        if not args:
            console.print("[red]❌ 请指定文件路径：/delete <文件路径>[/red]")
            return
        
        file_path = args.strip()
        try:
            result = self.file_skill.call('file_delete', {'file_path': file_path})
            console.print(f"[green]✅ 文件已删除：{file_path}[/green]")
        except Exception as e:
            console.print(f"[red]❌ 删除失败：{str(e)}[/red]")
    
    def _file_list(self, args: str):
        """列出文件"""
        dir_path = args.strip() if args else '.'
        try:
            result = self.file_skill.call('file_list', {'directory': dir_path})
            if isinstance(result, dict) and 'files' in result:
                files = result['files']
                console.print(f"\n[bold]目录：{dir_path}[/bold]\n")
                for f in files:
                    icon = "📁" if f.get('is_directory') else "📄"
                    console.print(f"  {icon} {f.get('name', '')}")
            else:
                console.print(f"[gray]{result}[/gray]")
        except Exception as e:
            console.print(f"[red]❌ 列出失败：{str(e)}[/red]")
    
    def _file_search(self, args: str):
        """搜索文件"""
        if not args:
            console.print("[red]❌ 用法：/search <关键词> [目录][/red]")
            return
        
        parts = args.split(maxsplit=1)
        pattern = parts[0]
        directory = parts[1] if len(parts) > 1 else '.'
        
        try:
            result = self.file_skill.call('file_search', {
                'pattern': pattern,
                'directory': directory
            })
            if isinstance(result, dict) and 'matches' in result:
                matches = result['matches']
                if matches:
                    console.print(f"\n[bold]找到 {len(matches)} 个匹配项:[/bold]\n")
                    for match in matches[:20]:  # 限制显示数量
                        console.print(f"  📄 {match}")
                else:
                    console.print("[yellow]未找到匹配的文件[/yellow]")
            else:
                console.print(f"[gray]{result}[/gray]")
        except Exception as e:
            console.print(f"[red]❌ 搜索失败：{str(e)}[/red]")
    
    def _handle_exec(self, args: str, is_shell=False):
        """执行代码"""
        if not args:
            cmd_type = "Shell" if is_shell else "Python"
            console.print(f"[red]❌ 请指定{cmd_type}代码：/{'shell' if is_shell else 'exec'} <代码>[/red]")
            return
        
        try:
            if is_shell:
                result = self.exec_skill.call('execute_shell', {'command': args})
            else:
                result = self.exec_skill.call('execute_python', {'code': args})
            
            if isinstance(result, dict):
                output = result.get('output', '')
                error = result.get('error', '')
                
                if output:
                    console.print(f"\n[bold]输出:[/bold]\n{output}")
                if error:
                    console.print(f"\n[bold red]错误:[/bold red]\n{error}")
            else:
                console.print(f"[gray]{result}[/gray]")
        except Exception as e:
            console.print(f"[red]❌ 执行失败：{str(e)}[/red]")
    
    def run(self):
        """运行交互界面"""
        while True:
            try:
                user_input = self.session.prompt(
                    '🤖 > ',
                    style='fg:cyan bold'
                ).strip()
                
                if not user_input:
                    continue
                
                cmd, args = self._parse_command(user_input)
                
                if cmd in ['exit', 'quit']:
                    console.print("[yellow]👋 再见！[/yellow]")
                    break
                elif cmd == 'help':
                    self._show_welcome()
                elif cmd == 'clear':
                    os.system('clear' if os.name != 'nt' else 'cls')
                elif cmd == 'review':
                    self._handle_review(args)
                elif cmd == 'analyze':
                    self._handle_analyze(args)
                elif cmd == 'explain':
                    self._handle_explain(args)
                elif cmd == 'generate':
                    self._handle_generate(args)
                elif cmd == 'refactor':
                    self._handle_refactor(args)
                elif cmd in ['read', 'write', 'append', 'delete', 'list', 'search']:
                    self._handle_file_command(cmd, args)
                elif cmd == 'exec':
                    self._handle_exec(args, is_shell=False)
                elif cmd == 'shell':
                    self._handle_exec(args, is_shell=True)
                else:
                    console.print(f"[red]❌ 未知命令：/{cmd}[/red]")
                    console.print("[yellow]输入 /help 查看可用命令[/yellow]")
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]按 Ctrl+D 或输入 /exit 退出[/yellow]")
            except EOFError:
                console.print("\n[yellow]👋 再见！[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]❌ 发生错误：{str(e)}[/red]")


def main():
    """主入口"""
    assistant = AICodingAssistant()
    assistant.run()


if __name__ == '__main__':
    main()
