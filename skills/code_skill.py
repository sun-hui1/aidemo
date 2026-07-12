# skills/code_skill.py
"""
代码技能 - 封装 CodeEngine 能力供 LLM 调用
提供代码分析、生成、审查、解释等功能
"""
from skills.base_skill import BaseSkill, SkillResult
from typing import List, Dict, Any
from engines.code_engine import CodeEngine


class CodeSkill(BaseSkill):
    """代码操作技能"""
    
    def __init__(self):
        super().__init__(
            name="code",
            description="提供代码分析、生成、审查、解释等核心能力。支持 Python/JavaScript 等多种语言。",
            version="1.0.0"
        )
        self.engine = CodeEngine()
    
    def get_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "code_analyze",
                    "description": "分析代码文件的结构、复杂度、函数、类等信息。适用于理解现有代码。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "要分析的代码文件路径"
                            },
                            "detail_level": {
                                "type": "string",
                                "description": "详细程度：brief（简要）或 detailed（详细）",
                                "enum": ["brief", "detailed"],
                                "default": "brief"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "code_generate",
                    "description": "根据描述生成代码。支持函数、类、模块等不同粒度的代码生成。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "代码功能描述"
                            },
                            "language": {
                                "type": "string",
                                "description": "编程语言",
                                "enum": ["python", "javascript", "typescript"],
                                "default": "python"
                            },
                            "template_type": {
                                "type": "string",
                                "description": "代码模板类型",
                                "enum": ["function", "class", "module"],
                                "default": "module"
                            },
                            "function_name": {
                                "type": "string",
                                "description": "函数名称（当 template_type 为 function 时）",
                                "default": None
                            },
                            "class_name": {
                                "type": "string",
                                "description": "类名称（当 template_type 为 class 时）",
                                "default": None
                            }
                        },
                        "required": ["description", "language"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "code_review",
                    "description": "审查代码质量，检查潜在问题、安全漏洞、最佳实践遵循情况等。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "要审查的代码文件路径"
                            },
                            "focus_areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "重点关注的审查领域",
                                "enum": ["security", "complexity", "style", "performance", "all"],
                                "default": ["all"]
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "code_explain",
                    "description": "解释代码功能和实现逻辑。适用于理解复杂代码或向他人讲解代码。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "要解释的代码文件路径"
                            },
                            "detail_level": {
                                "type": "string",
                                "description": "解释的详细程度",
                                "enum": ["brief", "detailed"],
                                "default": "brief"
                            },
                            "focus": {
                                "type": "string",
                                "description": "解释重点",
                                "enum": ["overall", "functions", "classes", "algorithms"],
                                "default": "overall"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "code_refactor",
                    "description": "重构代码以改进结构、性能或可读性。支持提取方法、简化条件等常见重构策略。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "要重构的代码文件路径"
                            },
                            "strategy": {
                                "type": "string",
                                "description": "重构策略",
                                "enum": ["extract_method", "simplify_condition", "rename_variable", "remove_duplication"],
                                "default": "extract_method"
                            },
                            "target_name": {
                                "type": "string",
                                "description": "目标名称（如新函数名、变量名等）",
                                "default": None
                            },
                            "start_line": {
                                "type": "integer",
                                "description": "起始行号（用于提取方法等）",
                                "default": None
                            },
                            "end_line": {
                                "type": "integer",
                                "description": "结束行号（用于提取方法等）",
                                "default": None
                            }
                        },
                        "required": ["file_path", "strategy"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "code_modify",
                    "description": "修改现有代码，如添加功能、修复 bug、优化性能等。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "要修改的代码文件路径"
                            },
                            "function_name": {
                                "type": "string",
                                "description": "要修改的函数名"
                            },
                            "changes": {
                                "type": "object",
                                "description": "修改内容描述",
                                "properties": {
                                    "add_params": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "新增参数"
                                    },
                                    "remove_params": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "移除参数"
                                    },
                                    "new_body_description": {
                                        "type": "string",
                                        "description": "新的函数体描述"
                                    }
                                }
                            }
                        },
                        "required": ["file_path", "function_name", "changes"]
                    }
                }
            }
        ]
    
    def call(self, tool_name: str, **kwargs) -> SkillResult:
        """执行具体的代码操作"""
        try:
            if tool_name == "analyze":
                return self._analyze_code(
                    file_path=kwargs.get("file_path"),
                    detail_level=kwargs.get("detail_level", "brief")
                )
            elif tool_name == "generate":
                return self._generate_code(
                    description=kwargs.get("description"),
                    language=kwargs.get("language", "python"),
                    template_type=kwargs.get("template_type", "module"),
                    function_name=kwargs.get("function_name"),
                    class_name=kwargs.get("class_name")
                )
            elif tool_name == "review":
                return self._review_code(
                    file_path=kwargs.get("file_path"),
                    focus_areas=kwargs.get("focus_areas", ["all"])
                )
            elif tool_name == "explain":
                return self._explain_code(
                    file_path=kwargs.get("file_path"),
                    detail_level=kwargs.get("detail_level", "brief"),
                    focus=kwargs.get("focus", "overall")
                )
            elif tool_name == "refactor":
                return self._refactor_code(
                    file_path=kwargs.get("file_path"),
                    strategy=kwargs.get("strategy"),
                    target_name=kwargs.get("target_name"),
                    start_line=kwargs.get("start_line"),
                    end_line=kwargs.get("end_line")
                )
            elif tool_name == "modify":
                return self._modify_code(
                    file_path=kwargs.get("file_path"),
                    function_name=kwargs.get("function_name"),
                    changes=kwargs.get("changes")
                )
            else:
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"未知工具：{tool_name}",
                    message=f"{self.name} 技能不包含此工具"
                )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="代码操作执行过程中发生错误"
            )
    
    def _analyze_code(self, file_path: str, detail_level: str) -> SkillResult:
        """分析代码"""
        try:
            result = self.engine.analyze_file(file_path)
            
            if "error" in result:
                return SkillResult(
                    success=False,
                    data=None,
                    error=result["error"],
                    message="代码分析失败"
                )
            
            # 根据详细程度过滤结果
            if detail_level == "brief":
                brief_result = {
                    "file": result.get("file"),
                    "language": result.get("language"),
                    "metrics": {
                        "loc": result.get("metrics", {}).get("loc", 0),
                        "functions": result.get("metrics", {}).get("functions", 0),
                        "classes": result.get("metrics", {}).get("classes", 0),
                        "complexity": result.get("metrics", {}).get("complexity", 0)
                    },
                    "function_names": [f["name"] for f in result.get("functions", [])],
                    "class_names": [c["name"] for c in result.get("classes", [])]
                }
                result = brief_result
            
            return SkillResult(
                success=True,
                data=result,
                error=None,
                message=f"✅ 代码分析完成：{result.get('language', 'unknown')} 文件，"
                       f"{result.get('metrics', {}).get('functions', 0)} 个函数，"
                       f"{result.get('metrics', {}).get('classes', 0)} 个类"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="代码分析异常"
            )
    
    def _generate_code(self, description: str, language: str, template_type: str, 
                      function_name: str = None, class_name: str = None) -> SkillResult:
        """生成代码"""
        try:
            kwargs = {
                "description": description
            }
            
            # 根据模板类型设置不同的参数
            if template_type == "function" and function_name:
                kwargs["template_type"] = "python_module"
                kwargs["function_name"] = function_name
            elif template_type == "class" and class_name:
                kwargs["template_type"] = "python_class"
                kwargs["class_name"] = class_name
            else:
                kwargs["template_type"] = "python_module"
            
            code = self.engine.generate_boilerplate(**kwargs)
            
            return SkillResult(
                success=True,
                data={"code": code, "language": language, "type": template_type},
                error=None,
                message=f"✅ 代码生成完成：{language} {template_type}"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="代码生成失败"
            )
    
    def _review_code(self, file_path: str, focus_areas: list) -> SkillResult:
        """审查代码"""
        try:
            result = self.engine.review_file(file_path)
            
            if "error" in result:
                return SkillResult(
                    success=False,
                    data=None,
                    error=result["error"],
                    message="代码审查失败"
                )
            
            # 根据关注领域过滤问题
            issues = result.get("issues", [])
            if "all" not in focus_areas:
                filtered_issues = [
                    issue for issue in issues 
                    if issue.get("category") in focus_areas
                ]
                result["issues"] = filtered_issues
            
            score = result.get("score", 0)
            issue_count = len(result.get("issues", []))
            
            return SkillResult(
                success=True,
                data=result,
                error=None,
                message=f"✅ 代码审查完成：得分 {score}/100，发现 {issue_count} 个问题"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="代码审查异常"
            )
    
    def _explain_code(self, file_path: str, detail_level: str, focus: str) -> SkillResult:
        """解释代码"""
        try:
            # 先读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            explanation = self.engine.explain_code(source_code, detail_level)
            
            # 根据关注点过滤
            if focus == "functions":
                explanation = {
                    "summary": explanation.get("summary"),
                    "functions": explanation.get("functions", [])
                }
            elif focus == "classes":
                explanation = {
                    "summary": explanation.get("summary"),
                    "classes": explanation.get("classes", [])
                }
            elif focus == "algorithms":
                # 提取算法相关信息
                explanation = {
                    "summary": explanation.get("summary"),
                    "metrics": explanation.get("metrics", {}),
                    "complexity_note": "高复杂度函数可能需要优化"
                }
            
            return SkillResult(
                success=True,
                data=explanation,
                error=None,
                message=f"✅ 代码解释完成"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="代码解释异常"
            )
    
    def _refactor_code(self, file_path: str, strategy: str, target_name: str = None,
                       start_line: int = None, end_line: int = None) -> SkillResult:
        """重构代码"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            kwargs = {}
            if target_name:
                kwargs["function_name"] = target_name
            if start_line:
                kwargs["start_line"] = start_line
            if end_line:
                kwargs["end_line"] = end_line
            
            result = self.engine.refactor_code(source_code, strategy, **kwargs)
            
            if result.get("success"):
                return SkillResult(
                    success=True,
                    data={
                        "original_code": source_code,
                        "refactored_code": result.get("code"),
                        "message": result.get("message")
                    },
                    error=None,
                    message=f"✅ 代码重构完成：{strategy}"
                )
            else:
                return SkillResult(
                    success=False,
                    data=None,
                    error=result.get("error"),
                    message="代码重构失败"
                )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="代码重构异常"
            )
    
    def _modify_code(self, file_path: str, function_name: str, changes: dict) -> SkillResult:
        """修改代码"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            modified_code = self.engine.modify_code(
                source_code,
                function_name,
                changes
            )
            
            return SkillResult(
                success=True,
                data={
                    "original_code": source_code,
                    "modified_code": modified_code,
                    "function_name": function_name,
                    "changes": changes
                },
                error=None,
                message=f"✅ 代码修改完成：函数 {function_name}"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="代码修改异常"
            )


# 自动注册
if __name__ == "__main__":
    from core.skill_registry import SkillRegistry
    registry = SkillRegistry()
    registry.register(CodeSkill)
