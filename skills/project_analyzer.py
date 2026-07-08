"""
项目分析器技能
自动扫描和理解项目结构、代码依赖、技术栈等信息
"""
import os
import json
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from datetime import datetime
from base_skill import BaseSkill, SkillResult


class ProjectAnalyzer(BaseSkill):
    """项目分析技能"""
    
    def __init__(self):
        super().__init__(
            name="project_analyzer",
            description="分析项目结构、识别技术栈、理解代码依赖关系",
            version="1.0.0"
        )
        self.supported_files = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text'
        }
        self.config_files = [
            'package.json', 'requirements.txt', 'setup.py', 'Cargo.toml',
            'go.mod', 'pom.xml', 'build.gradle', 'CMakeLists.txt',
            'Makefile', 'docker-compose.yml', 'Dockerfile',
            '.gitignore', 'README.md', 'config.json', 'settings.json'
        ]

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "scan_project_structure",
                "description": "扫描项目目录结构，返回文件树和统计信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "root_path": {
                            "type": "string",
                            "description": "项目根目录路径，默认为当前工作目录"
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "最大扫描深度，默认 5 层",
                            "default": 5
                        },
                        "include_hidden": {
                            "type": "boolean",
                            "description": "是否包含隐藏文件和目录",
                            "default": False
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "identify_tech_stack",
                "description": "识别项目使用的技术栈、框架和依赖",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "root_path": {
                            "type": "string",
                            "description": "项目根目录路径"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "analyze_dependencies",
                "description": "分析代码文件的依赖关系",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要分析的文件路径"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "是否递归分析所有依赖",
                            "default": False
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "find_similar_code",
                "description": "在项目中查找相似的代码模式或重复代码",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "要搜索的代码模式或关键词"
                        },
                        "file_extensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "限制搜索的文件扩展名列表"
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "是否区分大小写",
                            "default": False
                        }
                    },
                    "required": ["pattern"]
                }
            },
            {
                "name": "get_project_summary",
                "description": "获取项目的综合摘要报告",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "root_path": {
                            "type": "string",
                            "description": "项目根目录路径"
                        }
                    },
                    "required": []
                }
            }
        ]

    def scan_project_structure(self, root_path: Optional[str] = None, 
                               max_depth: int = 5, 
                               include_hidden: bool = False) -> SkillResult:
        """扫描项目结构"""
        try:
            if not root_path:
                root_path = os.getcwd()
            
            if not os.path.exists(root_path):
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"路径不存在：{root_path}",
                    message="请检查路径是否正确"
                )
            
            structure = {
                "root": root_path,
                "scanned_at": datetime.now().isoformat(),
                "tree": {},
                "statistics": {
                    "total_files": 0,
                    "total_dirs": 0,
                    "by_extension": {},
                    "total_size_bytes": 0
                }
            }
            
            def scan_dir(path: str, depth: int) -> Dict:
                if depth > max_depth:
                    return {"_truncated": True}
                
                result = {"_type": "directory"}
                try:
                    entries = sorted(os.listdir(path))
                    for entry in entries:
                        if not include_hidden and entry.startswith('.'):
                            continue
                        
                        full_path = os.path.join(path, entry)
                        
                        if os.path.isdir(full_path):
                            structure["statistics"]["total_dirs"] += 1
                            result[entry] = scan_dir(full_path, depth + 1)
                        else:
                            structure["statistics"]["total_files"] += 1
                            ext = os.path.splitext(entry)[1].lower()
                            structure["statistics"]["by_extension"][ext] = \
                                structure["statistics"]["by_extension"].get(ext, 0) + 1
                            
                            try:
                                size = os.path.getsize(full_path)
                                structure["statistics"]["total_size_bytes"] += size
                                result[entry] = {"_type": "file", "_size": size}
                            except:
                                result[entry] = {"_type": "file"}
                except PermissionError:
                    result["_error"] = "Permission denied"
                
                return result
            
            structure["tree"] = scan_dir(root_path, 0)
            
            # 格式化大小
            size_bytes = structure["statistics"]["total_size_bytes"]
            if size_bytes > 1024 * 1024:
                structure["statistics"]["total_size"] = f"{size_bytes / (1024*1024):.2f} MB"
            elif size_bytes > 1024:
                structure["statistics"]["total_size"] = f"{size_bytes / 1024:.2f} KB"
            else:
                structure["statistics"]["total_size"] = f"{size_bytes} B"
            
            return SkillResult(
                success=True,
                data=structure,
                error=None,
                message=f"扫描完成：{structure['statistics']['total_files']} 个文件，{structure['statistics']['total_dirs']} 个目录"
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="扫描项目结构失败"
            )

    def identify_tech_stack(self, root_path: Optional[str] = None) -> SkillResult:
        """识别技术栈"""
        try:
            if not root_path:
                root_path = os.getcwd()
            
            tech_stack = {
                "languages": set(),
                "frameworks": [],
                "dependencies": [],
                "tools": [],
                "config_files": []
            }
            
            # 语言映射
            language_indicators = {
                'python': ['requirements.txt', 'setup.py', '.py'],
                'javascript': ['package.json', '.js', 'node_modules'],
                'typescript': ['tsconfig.json', '.ts'],
                'java': ['pom.xml', 'build.gradle', '.java'],
                'go': ['go.mod', '.go'],
                'rust': ['Cargo.toml', '.rs'],
                'ruby': ['Gemfile', '.rb'],
                'php': ['composer.json', '.php'],
                'c++': ['CMakeLists.txt', '.cpp', '.hpp'],
                'c': ['.c', '.h']
            }
            
            # 框架指示器
            framework_patterns = {
                'django': ['django', 'settings.py', 'manage.py'],
                'flask': ['flask', 'app.py'],
                'react': ['react', 'jsx', 'ReactDOM'],
                'vue': ['vue', 'Vue.js'],
                'angular': ['angular', '@angular'],
                'spring': ['springframework', '@SpringBootApplication'],
                'express': ['express', 'app.listen']
            }
            
            # 扫描文件
            for root, dirs, files in os.walk(root_path):
                # 跳过隐藏目录和 node_modules 等大型目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
                
                for file in files:
                    if file.startswith('.') and file not in self.config_files:
                        continue
                    
                    file_path = os.path.join(root, file)
                    
                    # 检查配置文件
                    if file in self.config_files:
                        tech_stack["config_files"].append(file)
                    
                    # 识别语言
                    _, ext = os.path.splitext(file)
                    if ext in self.supported_files:
                        tech_stack["languages"].add(self.supported_files[ext])
                    
                    # 检查语言特定文件
                    for lang, indicators in language_indicators.items():
                        if any(file == ind or file.endswith(ind) for ind in indicators):
                            tech_stack["languages"].add(lang)
                    
                    # 读取小文件内容以识别框架
                    try:
                        if os.path.getsize(file_path) < 50 * 1024:  # 小于 50KB
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read(5000)  # 读取前 5KB
                                
                                for framework, patterns in framework_patterns.items():
                                    if any(pattern.lower() in content.lower() for pattern in patterns):
                                        if framework not in tech_stack["frameworks"]:
                                            tech_stack["frameworks"].append(framework)
                    except:
                        pass
            
            # 解析包管理文件
            if os.path.exists(os.path.join(root_path, 'package.json')):
                try:
                    with open(os.path.join(root_path, 'package.json'), 'r') as f:
                        pkg = json.load(f)
                        deps = list(pkg.get('dependencies', {}).keys())
                        dev_deps = list(pkg.get('devDependencies', {}).keys())
                        tech_stack["dependencies"].extend(deps[:10])
                        tech_stack["tools"].extend(dev_deps[:5])
                except:
                    pass
            
            if os.path.exists(os.path.join(root_path, 'requirements.txt')):
                try:
                    with open(os.path.join(root_path, 'requirements.txt'), 'r') as f:
                        deps = [line.split('==')[0].split('>=')[0].strip() 
                               for line in f if line.strip() and not line.startswith('#')]
                        tech_stack["dependencies"].extend(deps[:20])
                except:
                    pass
            
            result = {
                "languages": list(tech_stack["languages"]),
                "frameworks": tech_stack["frameworks"],
                "dependencies": tech_stack["dependencies"][:15],
                "tools": tech_stack["tools"][:10],
                "config_files": list(set(tech_stack["config_files"]))
            }
            
            return SkillResult(
                success=True,
                data=result,
                error=None,
                message=f"识别到 {len(result['languages'])} 种语言，{len(result['frameworks'])} 个框架"
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="识别技术栈失败"
            )

    def analyze_dependencies(self, file_path: str, recursive: bool = False) -> SkillResult:
        """分析文件依赖"""
        try:
            if not os.path.exists(file_path):
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"文件不存在：{file_path}",
                    message="请检查文件路径"
                )
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            imports = {
                "standard_library": [],
                "third_party": [],
                "local_modules": [],
                "imports_raw": []
            }
            
            _, ext = os.path.splitext(file_path)
            
            # Python 导入
            if ext == '.py':
                import re
                # import module
                for match in re.finditer(r'^import\s+([\w\.]+)', content, re.MULTILINE):
                    module = match.group(1).split('.')[0]
                    imports["imports_raw"].append(match.group(0))
                    imports["third_party"].append(module)
                
                # from module import ...
                for match in re.finditer(r'^from\s+([\w\.]+)\s+import', content, re.MULTILINE):
                    module = match.group(1).split('.')[0]
                    imports["imports_raw"].append(match.group(0))
                    if module in ['os', 'sys', 'json', 're', 'datetime', 'collections']:
                        imports["standard_library"].append(module)
                    elif module.startswith('.'):
                        imports["local_modules"].append(module)
                    else:
                        imports["third_party"].append(module)
            
            # JavaScript/TypeScript 导入
            elif ext in ['.js', '.ts']:
                import re
                # import ... from '...'
                for match in re.finditer(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', content):
                    path = match.group(1)
                    imports["imports_raw"].append(match.group(0))
                    if path.startswith('.') or path.startswith('/'):
                        imports["local_modules"].append(path)
                    else:
                        imports["third_party"].append(path.split('/')[0])
                
                # require('...')
                for match in re.finditer(r'require\([\'"]([^\'"]+)[\'"]\)', content):
                    path = match.group(1)
                    imports["imports_raw"].append(match.group(0))
                    if path.startswith('.') or path.startswith('/'):
                        imports["local_modules"].append(path)
                    else:
                        imports["third_party"].append(path.split('/')[0])
            
            # 去重
            imports["standard_library"] = list(set(imports["standard_library"]))
            imports["third_party"] = list(set(imports["third_party"]))
            imports["local_modules"] = list(set(imports["local_modules"]))
            
            return SkillResult(
                success=True,
                data={
                    "file": file_path,
                    "language": self.supported_files.get(ext, "unknown"),
                    "imports": imports,
                    "summary": {
                        "total_imports": len(imports["imports_raw"]),
                        "external_packages": len(imports["third_party"]),
                        "local_modules": len(imports["local_modules"])
                    }
                },
                error=None,
                message=f"分析完成：共 {len(imports['imports_raw'])} 个导入"
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="分析依赖失败"
            )

    def find_similar_code(self, pattern: str, 
                         file_extensions: Optional[List[str]] = None,
                         case_sensitive: bool = False) -> SkillResult:
        """查找相似代码"""
        try:
            results = []
            flags = 0 if case_sensitive else re.IGNORECASE
            
            import re
            regex = re.compile(re.escape(pattern), flags)
            
            for root, dirs, files in os.walk(os.getcwd()):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if file_extensions:
                        _, ext = os.path.splitext(file)
                        if ext not in file_extensions:
                            continue
                    
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            matches = regex.findall(content)
                            
                            if matches:
                                # 获取匹配的行
                                lines = content.split('\n')
                                match_lines = []
                                for i, line in enumerate(lines, 1):
                                    if regex.search(line):
                                        match_lines.append({
                                            "line_number": i,
                                            "content": line.strip()[:100]
                                        })
                                
                                results.append({
                                    "file": file_path,
                                    "match_count": len(matches),
                                    "lines": match_lines[:5]  # 最多显示 5 行
                                })
                    except:
                        continue
            
            return SkillResult(
                success=True,
                data={
                    "pattern": pattern,
                    "total_matches": len(results),
                    "files": results[:20]  # 最多返回 20 个文件
                },
                error=None,
                message=f"找到 {len(results)} 个匹配的文件"
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="搜索代码失败"
            )

    def get_project_summary(self, root_path: Optional[str] = None) -> SkillResult:
        """获取项目摘要"""
        try:
            # 组合多个分析结果
            structure_result = self.scan_project_structure(root_path)
            tech_result = self.identify_tech_stack(root_path)
            
            if not structure_result.success or not tech_result.success:
                return SkillResult(
                    success=False,
                    data=None,
                    error="无法完成完整的项目分析",
                    message="部分分析失败"
                )
            
            summary = {
                "generated_at": datetime.now().isoformat(),
                "overview": {
                    "root_path": root_path or os.getcwd(),
                    "total_files": structure_result.data["statistics"]["total_files"],
                    "total_dirs": structure_result.data["statistics"]["total_dirs"],
                    "total_size": structure_result.data["statistics"]["total_size"]
                },
                "tech_stack": tech_result.data,
                "file_distribution": structure_result.data["statistics"]["by_extension"],
                "recommendations": []
            }
            
            # 生成建议
            if 'python' in summary['tech_stack']['languages']:
                if 'requirements.txt' not in summary['tech_stack']['config_files']:
                    summary["recommendations"].append("建议创建 requirements.txt 管理 Python 依赖")
            
            if 'javascript' in summary['tech_stack']['languages']:
                if 'package.json' not in summary['tech_stack']['config_files']:
                    summary["recommendations"].append("建议创建 package.json 管理 Node.js 项目")
            
            if summary['overview']['total_files'] > 1000:
                summary["recommendations"].append("项目较大，建议考虑模块化拆分")
            
            if len(summary['tech_stack']['languages']) > 3:
                summary["recommendations"].append("项目使用多种语言，建议明确各模块职责")
            
            return SkillResult(
                success=True,
                data=summary,
                error=None,
                message="项目摘要生成完成"
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="生成项目摘要失败"
            )

    def call(self, tool_name: str, **kwargs) -> SkillResult:
        if tool_name == "scan_project_structure":
            return self.scan_project_structure(
                root_path=kwargs.get("root_path"),
                max_depth=kwargs.get("max_depth", 5),
                include_hidden=kwargs.get("include_hidden", False)
            )
        elif tool_name == "identify_tech_stack":
            return self.identify_tech_stack(
                root_path=kwargs.get("root_path")
            )
        elif tool_name == "analyze_dependencies":
            return self.analyze_dependencies(
                file_path=kwargs.get("file_path"),
                recursive=kwargs.get("recursive", False)
            )
        elif tool_name == "find_similar_code":
            return self.find_similar_code(
                pattern=kwargs.get("pattern"),
                file_extensions=kwargs.get("file_extensions"),
                case_sensitive=kwargs.get("case_sensitive", False)
            )
        elif tool_name == "get_project_summary":
            return self.get_project_summary(
                root_path=kwargs.get("root_path")
            )
        else:
            return SkillResult(
                success=False,
                data=None,
                error=f"未知工具：{tool_name}",
                message=f"{self.name} 技能不包含此工具"
            )
