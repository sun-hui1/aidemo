"""
代码审查器 - 检测代码问题、提供改进建议
"""
import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class CodeIssue:
    """代码问题"""
    severity: str  # 'error', 'warning', 'info', 'suggestion'
    category: str  # 'security', 'performance', 'style', 'bug', 'complexity'
    line: int
    column: int = 0
    message: str = ""
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


class CodeReviewer:
    """代码审查引擎"""
    
    def __init__(self):
        self.max_line_length = 120
        self.max_function_length = 50
        self.max_params = 5
        self.max_nested_depth = 4
    
    def review_file(self, file_path: str) -> Dict[str, Any]:
        """审查单个文件"""
        path = Path(file_path)
        if not path.exists():
            return {"error": f"文件不存在：{file_path}"}
        
        ext = path.suffix.lower()
        if ext == '.py':
            return self._review_python(path)
        elif ext in ['.js', '.ts']:
            return self._review_javascript(path)
        else:
            return self._review_generic(path)
    
    def _review_python(self, path: Path) -> Dict[str, Any]:
        """审查 Python 文件"""
        issues: List[CodeIssue] = []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            tree = ast.parse(content)
            
            # 执行各类检查
            issues.extend(self._check_security_issues(content, lines))
            issues.extend(self._check_code_smells(content, lines, tree))
            issues.extend(self._check_complexity(tree))
            issues.extend(self._check_style(lines))
            issues.extend(self._check_best_practices(tree, content))
            
            # 按严重程度排序
            severity_order = {'error': 0, 'warning': 1, 'info': 2, 'suggestion': 3}
            issues.sort(key=lambda x: (severity_order.get(x.severity, 4), x.line))
            
            # 生成摘要
            summary = {
                "total_issues": len(issues),
                "by_severity": {
                    "error": sum(1 for i in issues if i.severity == 'error'),
                    "warning": sum(1 for i in issues if i.severity == 'warning'),
                    "info": sum(1 for i in issues if i.severity == 'info'),
                    "suggestion": sum(1 for i in issues if i.severity == 'suggestion')
                },
                "by_category": {}
            }
            
            for issue in issues:
                summary["by_category"][issue.category] = \
                    summary["by_category"].get(issue.category, 0) + 1
            
            return {
                "file": str(path),
                "language": "python",
                "status": "reviewed",
                "summary": summary,
                "issues": [
                    {
                        "severity": i.severity,
                        "category": i.category,
                        "line": i.line,
                        "column": i.column,
                        "message": i.message,
                        "suggestion": i.suggestion,
                        "code_snippet": i.code_snippet
                    }
                    for i in issues[:50]  # 限制返回数量
                ]
            }
            
        except SyntaxError as e:
            return {
                "file": str(path),
                "status": "error",
                "error": f"语法错误：{e}",
                "line": e.lineno
            }
        except Exception as e:
            return {"error": f"审查失败：{str(e)}"}
    
    def _check_security_issues(self, content: str, lines: List[str]) -> List[CodeIssue]:
        """安全检查"""
        issues = []
        
        # 硬编码密码/密钥
        password_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'passwd\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in password_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    if 'os.environ' not in line and 'config' not in line:
                        issues.append(CodeIssue(
                            severity='error',
                            category='security',
                            line=i,
                            message="检测到可能的硬编码敏感信息",
                            suggestion="使用环境变量或配置文件管理敏感信息",
                            code_snippet=line.strip()
                        ))
        
        # eval/exec 使用
        for i, line in enumerate(lines, 1):
            if re.search(r'\b(eval|exec)\s*\(', line):
                issues.append(CodeIssue(
                    severity='warning',
                    category='security',
                    line=i,
                    message="使用 eval/exec 可能存在安全风险",
                    suggestion="考虑使用 ast.literal_eval 或其他安全替代方案",
                    code_snippet=line.strip()
                ))
        
        # SQL 注入风险
        sql_patterns = [
            r'execute\s*\(\s*f["\'].*?(?:SELECT|INSERT|UPDATE|DELETE)',
            r'execute\s*\(\s*["\'].*?%\s*.*?(?:SELECT|INSERT|UPDATE|DELETE)'
        ]
        for i, line in enumerate(lines, 1):
            for pattern in sql_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        severity='error',
                        category='security',
                        line=i,
                        message="可能存在 SQL 注入风险",
                        suggestion="使用参数化查询",
                        code_snippet=line.strip()
                    ))
        
        return issues
    
    def _check_code_smells(self, content: str, lines: List[str], 
                          tree: ast.AST) -> List[CodeIssue]:
        """代码异味检查"""
        issues = []
        
        # 过长的函数
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start = node.lineno
                end = getattr(node, 'end_lineno', start)
                length = end - start
                
                if length > self.max_function_length:
                    issues.append(CodeIssue(
                        severity='warning',
                        category='complexity',
                        line=start,
                        message=f"函数过长 ({length} 行，建议<{self.max_function_length})",
                        suggestion="考虑将函数拆分为更小的子函数",
                        code_snippet=f"def {node.name}(...)"
                    ))
                
                # 过多参数
                param_count = len(node.args.args)
                if param_count > self.max_params:
                    issues.append(CodeIssue(
                        severity='warning',
                        category='design',
                        line=start,
                        message=f"函数参数过多 ({param_count} 个，建议<{self.max_params})",
                        suggestion="考虑使用配置对象或将相关参数分组",
                        code_snippet=f"def {node.name}(...)"
                    ))
        
        # 重复代码块（简化检查）
        block_size = 5
        seen_blocks = {}
        for i in range(len(lines) - block_size):
            block = '\n'.join(lines[i:i+block_size]).strip()
            if block and not block.startswith('#'):
                if block in seen_blocks:
                    issues.append(CodeIssue(
                        severity='info',
                        category='duplication',
                        line=i+1,
                        message="发现重复代码块",
                        suggestion="考虑提取为公共函数",
                        code_snippet=block[:100] + "..."
                    ))
                else:
                    seen_blocks[block] = i
        
        return issues
    
    def _check_complexity(self, tree: ast.AST) -> List[CodeIssue]:
        """复杂度检查"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                
                if complexity > 10:
                    severity = 'error' if complexity > 20 else 'warning'
                    issues.append(CodeIssue(
                        severity=severity,
                        category='complexity',
                        line=node.lineno,
                        message=f"函数复杂度过高 (圈复杂度={complexity})",
                        suggestion="拆分函数或减少条件分支",
                        code_snippet=f"def {node.name}(...)"
                    ))
                
                # 嵌套深度
                max_depth = self._calculate_max_depth(node)
                if max_depth > self.max_nested_depth:
                    issues.append(CodeIssue(
                        severity='warning',
                        category='complexity',
                        line=node.lineno,
                        message=f"嵌套过深 (深度={max_depth}, 建议<={self.max_nested_depth})",
                        suggestion="使用提前返回或重构逻辑减少嵌套",
                        code_snippet=f"def {node.name}(...)"
                    ))
        
        return issues
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """计算圈复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                  ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _calculate_max_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """计算最大嵌套深度"""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                child_depth = self._calculate_max_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_max_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _check_style(self, lines: List[str]) -> List[CodeIssue]:
        """代码风格检查"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # 行长度
            if len(line) > self.max_line_length:
                issues.append(CodeIssue(
                    severity='info',
                    category='style',
                    line=i,
                    message=f"行过长 ({len(line)} 字符，建议<={self.max_line_length})",
                    suggestion="将长行拆分为多行",
                    code_snippet=line[:80] + "..."
                ))
            
            # 尾随空格
            if line.rstrip() != line:
                issues.append(CodeIssue(
                    severity='info',
                    category='style',
                    line=i,
                    message="行尾有多余空格",
                    suggestion="删除行尾空格",
                    code_snippet="<line>"
                ))
            
            # Tab 缩进
            if line.startswith('\t'):
                issues.append(CodeIssue(
                    severity='warning',
                    category='style',
                    line=i,
                    message="使用 Tab 缩进",
                    suggestion="使用 4 个空格代替 Tab",
                    code_snippet="<line>"
                ))
        
        return issues
    
    def _check_best_practices(self, tree: ast.AST, content: str) -> List[CodeIssue]:
        """最佳实践检查"""
        issues = []
        
        # 检查是否有 docstring
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if not docstring and isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    issues.append(CodeIssue(
                        severity='info',
                        category='documentation',
                        line=node.lineno,
                        message=f"{'函数' if isinstance(node, ast.FunctionDef) else '类'}缺少文档字符串",
                        suggestion="添加文档字符串说明用途",
                        code_snippet=f"{'def' if isinstance(node, ast.FunctionDef) else 'class'} {node.name}..."
                    ))
        
        # 裸 except
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append(CodeIssue(
                        severity='warning',
                        category='error_handling',
                        line=node.lineno,
                        message="使用裸 except",
                        suggestion="指定具体的异常类型",
                        code_snippet="except:"
                    ))
        
        # 可变默认参数
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults + node.args.kw_defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append(CodeIssue(
                            severity='warning',
                            category='bug',
                            line=node.lineno,
                            message="使用可变对象作为默认参数",
                            suggestion="使用 None 并在函数体内初始化",
                            code_snippet=f"def {node.name}(...)"
                        ))
        
        return issues
    
    def _review_javascript(self, path: Path) -> Dict[str, Any]:
        """审查 JavaScript 文件（基础版本）"""
        issues = []
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
        
        # 简单检查
        for i, line in enumerate(lines, 1):
            if 'var ' in line:
                issues.append(CodeIssue(
                    severity='info',
                    category='style',
                    line=i,
                    message="使用 var 声明变量",
                    suggestion="使用 let 或 const",
                    code_snippet=line.strip()
                ))
            
            if 'console.log' in line:
                issues.append(CodeIssue(
                    severity='info',
                    category='debugging',
                    line=i,
                    message="存在 console.log",
                    suggestion="生产环境应移除调试输出",
                    code_snippet=line.strip()
                ))
        
        return {
            "file": str(path),
            "language": "javascript" if path.suffix == '.js' else "typescript",
            "status": "reviewed",
            "summary": {
                "total_issues": len(issues),
                "by_severity": {
                    "error": sum(1 for i in issues if i.severity == 'error'),
                    "warning": sum(1 for i in issues if i.severity == 'warning'),
                    "info": sum(1 for i in issues if i.severity == 'info')
                }
            },
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "line": i.line,
                    "message": i.message,
                    "suggestion": i.suggestion
                }
                for i in issues[:30]
            ]
        }
    
    def _review_generic(self, path: Path) -> Dict[str, Any]:
        """通用文件审查"""
        return {
            "file": str(path),
            "status": "skipped",
            "message": "不支持的文件类型，跳过详细审查"
        }
    
    def get_quick_fixes(self, issue: Dict[str, Any]) -> Optional[str]:
        """为问题提供快速修复建议"""
        category = issue.get('category', '')
        message = issue.get('message', '')
        
        fixes = {
            'security': "立即修复：使用环境变量存储敏感信息",
            'complexity': "重构建议：提取子函数降低复杂度",
            'style': "运行格式化工具自动修复",
            'bug': "高风险：可能导致运行时错误"
        }
        
        return fixes.get(category)
