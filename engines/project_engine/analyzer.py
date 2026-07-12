"""
项目分析器引擎 - 自动扫描和理解项目结构、代码依赖、技术栈等信息
"""
import os
import json
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from datetime import datetime


class ProjectAnalyzer:
    """项目分析引擎"""
    
    def __init__(self):
        self.supported_files = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.go': 'go',
            '.rs': 'rust', '.rb': 'ruby', '.php': 'php', '.html': 'html',
            '.css': 'css', '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
            '.md': 'markdown', '.txt': 'text'
        }
        self.config_files = [
            'package.json', 'requirements.txt', 'setup.py', 'Cargo.toml',
            'go.mod', 'pom.xml', 'build.gradle', 'CMakeLists.txt',
            'Makefile', 'docker-compose.yml', 'Dockerfile',
            '.gitignore', 'README.md', 'config.json', 'settings.json'
        ]

    def scan_project_structure(self, root_path: Optional[str] = None, 
                               max_depth: int = 5, include_hidden: bool = False) -> Dict[str, Any]:
        """扫描项目结构"""
        try:
            if not root_path:
                root_path = os.getcwd()
            if not os.path.exists(root_path):
                return {"success": False, "error": f"路径不存在：{root_path}"}
            
            structure = {"root": root_path, "scanned_at": datetime.now().isoformat(), "tree": {},
                        "statistics": {"total_files": 0, "total_dirs": 0, "by_extension": {}, "total_size_bytes": 0}}
            
            def scan_dir(path: str, depth: int) -> Dict:
                if depth > max_depth:
                    return {"_truncated": True}
                result = {"_type": "directory"}
                try:
                    for entry in sorted(os.listdir(path)):
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
            size_bytes = structure["statistics"]["total_size_bytes"]
            if size_bytes > 1024 * 1024:
                structure["statistics"]["total_size"] = f"{size_bytes / (1024*1024):.2f} MB"
            elif size_bytes > 1024:
                structure["statistics"]["total_size"] = f"{size_bytes / 1024:.2f} KB"
            else:
                structure["statistics"]["total_size"] = f"{size_bytes} B"
            
            return {"success": True, "data": structure,
                    "message": f"扫描完成：{structure['statistics']['total_files']} 个文件"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def identify_tech_stack(self, root_path: Optional[str] = None) -> Dict[str, Any]:
        """识别技术栈"""
        try:
            if not root_path:
                root_path = os.getcwd()
            tech_stack = {"languages": set(), "frameworks": [], "dependencies": [], "tools": [], "config_files": []}
            language_indicators = {'python': ['requirements.txt', 'setup.py', '.py'],
                                   'javascript': ['package.json', '.js'], 'typescript': ['tsconfig.json', '.ts'],
                                   'java': ['pom.xml', 'build.gradle', '.java'], 'go': ['go.mod', '.go'],
                                   'rust': ['Cargo.toml', '.rs']}
            framework_patterns = {'django': ['django', 'settings.py'], 'flask': ['flask', 'app.py'],
                                  'react': ['react', 'jsx'], 'vue': ['vue', 'Vue.js']}
            
            for root, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
                for file in files:
                    if file.startswith('.') and file not in self.config_files:
                        continue
                    file_path = os.path.join(root, file)
                    if file in self.config_files:
                        tech_stack["config_files"].append(file)
                    _, ext = os.path.splitext(file)
                    if ext in self.supported_files:
                        tech_stack["languages"].add(self.supported_files[ext])
                    for lang, indicators in language_indicators.items():
                        if any(file == ind or file.endswith(ind) for ind in indicators):
                            tech_stack["languages"].add(lang)
                    try:
                        if os.path.getsize(file_path) < 50 * 1024:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read(5000)
                                for framework, patterns in framework_patterns.items():
                                    if any(pattern.lower() in content.lower() for pattern in patterns):
                                        if framework not in tech_stack["frameworks"]:
                                            tech_stack["frameworks"].append(framework)
                    except:
                        pass
            
            pkg_path = os.path.join(root_path, 'package.json')
            if os.path.exists(pkg_path):
                try:
                    with open(pkg_path, 'r') as f:
                        pkg = json.load(f)
                        tech_stack["dependencies"].extend(list(pkg.get('dependencies', {}).keys())[:10])
                except:
                    pass
            
            req_path = os.path.join(root_path, 'requirements.txt')
            if os.path.exists(req_path):
                try:
                    with open(req_path, 'r') as f:
                        deps = [line.split('==')[0].split('>=')[0].strip() for line in f if line.strip() and not line.startswith('#')]
                        tech_stack["dependencies"].extend(deps[:20])
                except:
                    pass
            
            return {"success": True, "data": {"languages": list(tech_stack["languages"]),
                                              "frameworks": tech_stack["frameworks"],
                                              "dependencies": tech_stack["dependencies"][:15],
                                              "config_files": list(set(tech_stack["config_files"]))}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_dependencies(self, file_path: str) -> Dict[str, Any]:
        """分析文件依赖"""
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": f"文件不存在：{file_path}"}
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            imports = {"standard_library": [], "third_party": [], "local_modules": [], "imports_raw": []}
            _, ext = os.path.splitext(file_path)
            import re
            if ext == '.py':
                for match in re.finditer(r'^import\s+([\w\.]+)', content, re.MULTILINE):
                    module = match.group(1).split('.')[0]
                    imports["imports_raw"].append(match.group(0))
                    imports["third_party"].append(module)
                for match in re.finditer(r'^from\s+([\w\.]+)\s+import', content, re.MULTILINE):
                    module = match.group(1).split('.')[0]
                    imports["imports_raw"].append(match.group(0))
                    if module in ['os', 'sys', 'json', 're', 'datetime']:
                        imports["standard_library"].append(module)
                    elif module.startswith('.'):
                        imports["local_modules"].append(module)
                    else:
                        imports["third_party"].append(module)
            elif ext in ['.js', '.ts']:
                for match in re.finditer(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', content):
                    path = match.group(1)
                    imports["imports_raw"].append(match.group(0))
                    if path.startswith('.'):
                        imports["local_modules"].append(path)
                    else:
                        imports["third_party"].append(path)
            return {"success": True, "data": {"file": file_path, "imports": imports}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_similar_code(self, pattern: str, file_extensions: Optional[List[str]] = None,
                         case_sensitive: bool = False) -> Dict[str, Any]:
        """查找相似代码"""
        try:
            import re
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
            results = []
            extensions = file_extensions or list(self.supported_files.keys())
            for ext in extensions:
                for file_path in Path(os.getcwd()).rglob(f"*{ext}"):
                    if any(part.startswith('.') or part in ['node_modules', '__pycache__'] for part in file_path.parts):
                        continue
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            matches = regex.findall(content)
                            if matches:
                                results.append({"file": str(file_path), "matches": len(matches)})
                    except:
                        pass
            return {"success": True, "data": {"pattern": pattern, "total_matches": len(results), "files": results[:20]}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_project_summary(self, root_path: Optional[str] = None) -> Dict[str, Any]:
        """获取项目摘要"""
        try:
            structure_result = self.scan_project_structure(root_path)
            tech_result = self.identify_tech_stack(root_path)
            if not structure_result.get("success") or not tech_result.get("success"):
                return {"success": False, "error": "无法获取项目信息"}
            structure_data = structure_result.get("data", {})
            tech_data = tech_result.get("data", {})
            summary = {"root": structure_data.get("root", root_path or os.getcwd()),
                       "generated_at": datetime.now().isoformat(),
                       "statistics": structure_data.get("statistics", {}),
                       "tech_stack": {"languages": tech_data.get("languages", []),
                                      "frameworks": tech_data.get("frameworks", [])},
                       "health_indicators": {"has_readme": "README.md" in tech_data.get("config_files", []),
                                             "has_gitignore": ".gitignore" in tech_data.get("config_files", [])}}
            return {"success": True, "data": summary}
        except Exception as e:
            return {"success": False, "error": str(e)}
