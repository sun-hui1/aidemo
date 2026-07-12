"""
代码分析器 - 解析代码结构、依赖、复杂度等
"""
import ast
import os
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class CodeMetrics:
    """代码度量指标"""
    loc: int = 0  # 代码行数
    blank_lines: int = 0
    comment_lines: int = 0
    functions: int = 0
    classes: int = 0
    imports: int = 0
    complexity: int = 0  # 圈复杂度
    max_depth: int = 0  # 最大嵌套深度


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    start_line: int
    end_line: int
    args: List[str]
    docstring: Optional[str] = None
    complexity: int = 1
    calls: List[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    start_line: int
    end_line: int
    methods: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


class CodeAnalyzer:
    """代码静态分析引擎"""
    
    def __init__(self):
        self.supported_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs'}
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """分析单个文件"""
        path = Path(file_path)
        if not path.exists():
            return {"error": f"文件不存在：{file_path}"}
        
        ext = path.suffix.lower()
        if ext == '.py':
            return self._analyze_python(path)
        elif ext in ['.js', '.ts']:
            return self._analyze_javascript(path)
        else:
            return self._analyze_generic(path)
    
    def _analyze_python(self, path: Path) -> Dict[str, Any]:
        """分析 Python 文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            metrics = self._calculate_python_metrics(tree, content)
            functions = self._extract_functions(tree)
            classes = self._extract_classes(tree)
            imports = self._extract_imports(tree)
            
            return {
                "file": str(path),
                "language": "python",
                "metrics": {
                    "loc": metrics.loc,
                    "blank_lines": metrics.blank_lines,
                    "comment_lines": metrics.comment_lines,
                    "functions": metrics.functions,
                    "classes": metrics.classes,
                    "imports": metrics.imports,
                    "complexity": metrics.complexity,
                    "max_depth": metrics.max_depth
                },
                "functions": [
                    {
                        "name": f.name,
                        "line": f.start_line,
                        "args": f.args,
                        "complexity": f.complexity,
                        "docstring": f.docstring
                    }
                    for f in functions
                ],
                "classes": [
                    {
                        "name": c.name,
                        "line": c.start_line,
                        "methods": c.methods,
                        "bases": c.bases,
                        "docstring": c.docstring
                    }
                    for c in classes
                ],
                "imports": imports,
                "structure": "ok"
            }
        except SyntaxError as e:
            return {"error": f"语法错误：{e}", "line": e.lineno}
        except Exception as e:
            return {"error": f"分析失败：{str(e)}"}
    
    def _calculate_python_metrics(self, tree: ast.AST, content: str) -> CodeMetrics:
        """计算 Python 代码度量"""
        metrics = CodeMetrics()
        lines = content.splitlines()
        
        metrics.loc = len(lines)
        metrics.blank_lines = sum(1 for line in lines if not line.strip())
        metrics.comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics.functions += 1
                metrics.complexity += self._calculate_function_complexity(node)
            elif isinstance(node, ast.ClassDef):
                metrics.classes += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                metrics.imports += 1
        
        return metrics
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """计算函数圈复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                  ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _extract_functions(self, tree: ast.AST) -> List[FunctionInfo]:
        """提取函数信息"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                args = [arg.arg for arg in node.args.args]
                docstring = ast.get_docstring(node)
                functions.append(FunctionInfo(
                    name=node.name,
                    start_line=node.lineno,
                    end_line=getattr(node, 'end_lineno', node.lineno),
                    args=args,
                    docstring=docstring,
                    complexity=self._calculate_function_complexity(node)
                ))
        return functions
    
    def _extract_classes(self, tree: ast.AST) -> List[ClassInfo]:
        """提取类信息"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [base.id if hasattr(base, 'id') else str(base) 
                        for base in node.bases]
                methods = [n.name for n in node.body 
                          if isinstance(n, ast.FunctionDef)]
                docstring = ast.get_docstring(node)
                classes.append(ClassInfo(
                    name=node.name,
                    start_line=node.lineno,
                    end_line=getattr(node, 'end_lineno', node.lineno),
                    methods=methods,
                    bases=bases,
                    docstring=docstring
                ))
        return classes
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, str]]:
        """提取导入信息"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append({
                        "type": "from",
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "level": node.level
                    })
        return imports
    
    def _analyze_javascript(self, path: Path) -> Dict[str, Any]:
        """分析 JavaScript/TypeScript 文件（基础版本）"""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.splitlines()
        
        # 简单的正则匹配
        functions = re.findall(r'function\s+(\w+)\s*\(', content)
        classes = re.findall(r'class\s+(\w+)', content)
        imports = re.findall(r'^(?:import|export)\s+.*$', content, re.MULTILINE)
        
        return {
            "file": str(path),
            "language": "javascript" if path.suffix == '.js' else "typescript",
            "metrics": {
                "loc": len(lines),
                "functions": len(functions),
                "classes": len(classes),
                "imports": len(imports)
            },
            "functions": [{"name": name} for name in functions],
            "classes": [{"name": name} for name in classes],
            "imports": imports[:20]
        }
    
    def _analyze_generic(self, path: Path) -> Dict[str, Any]:
        """通用文件分析"""
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.splitlines()
        return {
            "file": str(path),
            "language": "unknown",
            "metrics": {
                "loc": len(lines),
                "size_bytes": len(content.encode('utf-8'))
            }
        }
    
    def analyze_directory(self, dir_path: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """分析目录中所有代码文件"""
        path = Path(dir_path)
        if not path.exists():
            return {"error": f"目录不存在：{dir_path}"}
        
        exts = extensions or list(self.supported_extensions)
        results = {
            "directory": str(path),
            "files": {},
            "summary": {
                "total_files": 0,
                "total_loc": 0,
                "total_functions": 0,
                "total_classes": 0,
                "by_language": {}
            }
        }
        
        for ext in exts:
            for file_path in path.rglob(f"*{ext}"):
                # 跳过隐藏目录和常见忽略目录
                if any(part.startswith('.') or part in ['node_modules', '__pycache__', 'venv', 'build', 'dist']
                      for part in file_path.parts):
                    continue
                
                analysis = self.analyze_file(str(file_path))
                if "error" not in analysis:
                    rel_path = str(file_path.relative_to(path))
                    results["files"][rel_path] = analysis
                    results["summary"]["total_files"] += 1
                    
                    metrics = analysis.get("metrics", {})
                    results["summary"]["total_loc"] += metrics.get("loc", 0)
                    results["summary"]["total_functions"] += metrics.get("functions", 0)
                    results["summary"]["total_classes"] += metrics.get("classes", 0)
                    
                    lang = analysis.get("language", "unknown")
                    results["summary"]["by_language"][lang] = \
                        results["summary"]["by_language"].get(lang, 0) + 1
        
        return results
