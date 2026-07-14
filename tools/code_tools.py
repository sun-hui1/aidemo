# tools/code_tools.py
"""
代码工具模块 - 提供代码生成、审查等独立工具
此模块将 CodeEngine 的核心能力封装为独立可调用的工具函数
适用于不通过 Skill 系统直接调用的场景
"""
from typing import List, Dict, Any, Optional
from engines.code_engine import CodeEngine


class CodeTools:
    """
    代码工具集合
    提供静态方法形式的代码操作工具，无需实例化即可使用
    """
    
    _engine = None
    
    @classmethod
    def _get_engine(cls) -> CodeEngine:
        """懒加载获取引擎实例"""
        if cls._engine is None:
            cls._engine = CodeEngine()
        return cls._engine
    
    # ==================== 代码分析工具 ====================
    
    @staticmethod
    def analyze_file(file_path: str, detail_level: str = "brief") -> Dict[str, Any]:
        """
        分析代码文件
        
        Args:
            file_path: 文件路径
            detail_level: 详细程度 (brief/detailed)
            
        Returns:
            分析结果字典
        """
        engine = CodeTools._get_engine()
        result = engine.analyze_file(file_path)
        
        if detail_level == "brief" and "metrics" in result:
            return {
                "file": result.get("file"),
                "language": result.get("language"),
                "metrics": {
                    "loc": result["metrics"].get("loc", 0),
                    "functions": result["metrics"].get("functions", 0),
                    "classes": result["metrics"].get("classes", 0),
                    "complexity": result["metrics"].get("complexity", 0)
                },
                "function_names": [f["name"] for f in result.get("functions", [])],
                "class_names": [c["name"] for c in result.get("classes", [])]
            }
        
        return result
    
    @staticmethod
    def analyze_code(source_code: str, language: str = "python") -> Dict[str, Any]:
        """
        分析代码字符串
        
        Args:
            source_code: 源代码字符串
            language: 编程语言
            
        Returns:
            分析结果字典
        """
        engine = CodeTools._get_engine()
        return engine.analyze_code(source_code)
    
    # ==================== 代码生成工具 ====================
    
    @staticmethod
    def generate_function(description: str, function_name: str, 
                         language: str = "python") -> str:
        """
        生成函数代码
        
        Args:
            description: 功能描述
            function_name: 函数名
            language: 编程语言
            
        Returns:
            生成的代码字符串
        """
        engine = CodeTools._get_engine()
        return engine.generate_boilerplate(
            template_type="python_module",
            description=description,
            function_name=function_name
        )
    
    @staticmethod
    def generate_class(description: str, class_name: str,
                      language: str = "python") -> str:
        """
        生成类代码
        
        Args:
            description: 功能描述
            class_name: 类名
            language: 编程语言
            
        Returns:
            生成的代码字符串
        """
        engine = CodeTools._get_engine()
        return engine.generate_boilerplate(
            template_type="python_class",
            description=description,
            class_name=class_name
        )
    
    @staticmethod
    def generate_module(description: str, language: str = "python") -> str:
        """
        生成模块代码
        
        Args:
            description: 功能描述
            language: 编程语言
            
        Returns:
            生成的代码字符串
        """
        engine = CodeTools._get_engine()
        return engine.generate_boilerplate(
            template_type="python_module",
            description=description
        )
    
    # ==================== 代码审查工具 ====================
    
    @staticmethod
    def review_file(file_path: str, 
                   focus_areas: List[str] = None) -> Dict[str, Any]:
        """
        审查代码文件
        
        Args:
            file_path: 文件路径
            focus_areas: 重点关注领域 [security, complexity, style, performance]
            
        Returns:
            审查结果字典
        """
        engine = CodeTools._get_engine()
        result = engine.review_file(file_path)
        
        if focus_areas and "all" not in focus_areas:
            issues = result.get("issues", [])
            filtered = [i for i in issues if i.get("category") in focus_areas]
            result["issues"] = filtered
        
        # 计算得分（如果没有的话）
        if "score" not in result:
            issues = result.get("issues", [])
            error_count = sum(1 for i in issues if i.get("severity") == "error")
            warning_count = sum(1 for i in issues if i.get("severity") == "warning")
            score = max(0, 100 - error_count * 20 - warning_count * 5)
            result["score"] = score
        
        return result
    
    @staticmethod
    def review_code(source_code: str,
                   focus_areas: List[str] = None) -> Dict[str, Any]:
        """
        审查代码字符串
        
        Args:
            source_code: 源代码字符串
            focus_areas: 重点关注领域
            
        Returns:
            审查结果字典
        """
        engine = CodeTools._get_engine()
        result = engine.review_code(source_code)
        
        if focus_areas and "all" not in focus_areas:
            issues = result.get("issues", [])
            filtered = [i for i in issues if i.get("category") in focus_areas]
            result["issues"] = filtered
        
        # 计算得分（如果没有的话）
        if "score" not in result:
            issues = result.get("issues", [])
            error_count = sum(1 for i in issues if i.get("severity") == "error")
            warning_count = sum(1 for i in issues if i.get("severity") == "warning")
            score = max(0, 100 - error_count * 20 - warning_count * 5)
            result["score"] = score
        
        return result
    
    @staticmethod
    def check_security(source_code: str) -> List[Dict[str, Any]]:
        """
        安全检查
        
        Args:
            source_code: 源代码字符串
            
        Returns:
            安全问题列表
        """
        engine = CodeTools._get_engine()
        return engine.check_security(source_code)
    
    @staticmethod
    def check_complexity(source_code: str) -> List[Dict[str, Any]]:
        """
        复杂度检查
        
        Args:
            source_code: 源代码字符串
            
        Returns:
            复杂度问题列表
        """
        engine = CodeTools._get_engine()
        return engine.check_complexity(source_code)
    
    # ==================== 代码重构工具 ====================
    
    @staticmethod
    def refactor_extract_method(source_code: str, start_line: int, 
                               end_line: int, new_method_name: str) -> Dict[str, Any]:
        """
        提取方法重构
        
        Args:
            source_code: 源代码字符串
            start_line: 起始行号
            end_line: 结束行号
            new_method_name: 新方法名
            
        Returns:
            重构结果
        """
        engine = CodeTools._get_engine()
        return engine.refactor_code(
            source_code,
            strategy="extract_method",
            start_line=start_line,
            end_line=end_line,
            new_method_name=new_method_name
        )
    
    # ==================== 代码解释工具 ====================
    
    @staticmethod
    def explain_code(source_code: str, detail_level: str = "brief",
                    focus: str = "overall") -> Dict[str, Any]:
        """
        解释代码
        
        Args:
            source_code: 源代码字符串
            detail_level: 详细程度 (brief/detailed)
            focus: 解释重点 (overall/functions/classes/algorithms)
            
        Returns:
            解释结果字典
        """
        engine = CodeTools._get_engine()
        result = engine.explain_code(source_code, detail_level)
        
        if focus != "overall":
            if focus == "functions":
                return {"functions": result.get("functions", [])}
            elif focus == "classes":
                return {"classes": result.get("classes", [])}
            elif focus == "algorithms":
                return {
                    "summary": result.get("summary"),
                    "metrics": result.get("metrics", {})
                }
        
        return result
    
    # ==================== 代码修改工具 ====================
    
    @staticmethod
    def modify_function(code: str, function_name: str,
                       changes: Dict[str, Any]) -> str:
        """
        修改函数代码
        
        Args:
            code: 源代码字符串
            function_name: 函数名
            changes: 修改内容 {add_params, remove_params, new_body_description}
            
        Returns:
            修改后的代码
        """
        engine = CodeTools._get_engine()
        return engine.modify_code(code, function_name, changes)
    
    @staticmethod
    def add_import(code: str, module: str, names: List[str] = None) -> str:
        """
        添加导入语句
        
        Args:
            code: 源代码字符串
            module: 模块名
            names: 导入的名称列表
            
        Returns:
            添加导入后的代码
        """
        engine = CodeTools._get_engine()
        return engine.add_import(code, module, names)


# 便捷函数导出
analyze_file = CodeTools.analyze_file
analyze_code = CodeTools.analyze_code
generate_function = CodeTools.generate_function
generate_class = CodeTools.generate_class
generate_module = CodeTools.generate_module
review_file = CodeTools.review_file
review_code = CodeTools.review_code
check_security = CodeTools.check_security
check_complexity = CodeTools.check_complexity
refactor_extract_method = CodeTools.refactor_extract_method
explain_code = CodeTools.explain_code
modify_function = CodeTools.modify_function
add_import = CodeTools.add_import

__all__ = [
    'CodeTools',
    'analyze_file',
    'analyze_code',
    'generate_function',
    'generate_class',
    'generate_module',
    'review_file',
    'review_code',
    'check_security',
    'check_complexity',
    'refactor_extract_method',
    'explain_code',
    'modify_function',
    'add_import'
]
