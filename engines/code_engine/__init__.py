"""
代码引擎 - 提供代码分析、生成、修改、审查等核心能力

这是 AI 代码助手的中心模块，包含：
- 代码结构分析
- 代码生成与补全
- 代码重构建议
- Bug 检测与修复
- 复杂度分析
"""
from .analyzer import CodeAnalyzer
from .generator import CodeGenerator
from .reviewer import CodeReviewer


class CodeEngine:
    """
    代码引擎 - 统一入口
    封装代码分析、生成、审查三大核心能力
    """
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.generator = CodeGenerator()
        self.reviewer = CodeReviewer()
    
    # ==================== 分析能力 ====================
    
    def analyze_code(self, source_code: str, file_name: str = "<source>"):
        """分析代码结构和质量"""
        # 临时写入文件以复用 analyze_file 逻辑
        import tempfile
        import os
        
        ext = ".py"
        with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
            f.write(source_code)
            temp_path = f.name
        
        try:
            result = self.analyzer.analyze_file(temp_path)
            if "file" in result:
                result["file"] = file_name
            return result
        finally:
            os.unlink(temp_path)
    
    def analyze_file(self, file_path: str):
        """分析文件"""
        return self.analyzer.analyze_file(file_path)
    
    def get_code_metrics(self, source_code: str):
        """获取代码度量指标"""
        result = self.analyze_code(source_code)
        return result.get("metrics", {})
    
    def get_code_structure(self, source_code: str):
        """获取代码结构"""
        result = self.analyze_code(source_code)
        return {
            "imports": result.get("imports", []),
            "functions": result.get("functions", []),
            "classes": result.get("classes", [])
        }
    
    # ==================== 生成能力 ====================
    
    def generate_code(self, description: str, language: str = "python", **kwargs):
        """根据描述生成代码"""
        template_type = kwargs.get('template_type', 'python_module')
        return self.generator.generate_boilerplate(template_type, description=description, **kwargs)
    
    def generate_boilerplate(self, template_type: str, **kwargs):
        """生成代码模板"""
        return self.generator.generate_boilerplate(template_type, **kwargs)
    
    def generate_function(self, name: str, args: list, body: str, docstring: str = None):
        """生成函数代码"""
        return self.generator.generate_function(name, args, body, docstring)
    
    def generate_class(self, name: str, bases: list = None, methods: list = None):
        """生成类代码"""
        return self.generator.generate_class(name, bases, methods=methods)
    
    def modify_code(self, code: str, function_name: str, changes: dict):
        """修改现有代码"""
        return self.generator.modify_function(code, function_name, changes)
    
    def add_import(self, code: str, module: str, names: list = None):
        """添加导入语句"""
        import_stmt = self.generator.generate_import_statement(module, names)
        return self.generator.add_import_to_file(code, import_stmt)
    
    # ==================== 审查能力 ====================
    
    def review_code(self, source_code: str, file_path: str = "<source>"):
        """审查代码质量"""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source_code)
            temp_path = f.name
        
        try:
            result = self.reviewer.review_file(temp_path)
            if "file" in result:
                result["file"] = file_path
            return result
        finally:
            os.unlink(temp_path)
    
    def review_file(self, file_path: str):
        """审查文件"""
        return self.reviewer.review_file(file_path)
    
    def check_security(self, source_code: str):
        """安全检查"""
        result = self.review_code(source_code)
        issues = result.get("issues", [])
        return [i for i in issues if i.get("category") == "security"]
    
    def check_complexity(self, source_code: str):
        """复杂度检查"""
        result = self.review_code(source_code)
        issues = result.get("issues", [])
        return [i for i in issues if i.get("category") == "complexity"]
    
    # ==================== 综合能力 ====================
    
    def refactor_code(self, source_code: str, strategy: str = "extract_method", **kwargs):
        """重构代码"""
        if strategy == "extract_method":
            new_code, message = self.generator.refactor_extract_method(
                source_code,
                kwargs.get("function_name", "func"),
                kwargs.get("start_line", 1),
                kwargs.get("end_line", 10),
                kwargs.get("new_method_name", "extracted_method")
            )
            return {"success": True, "code": new_code, "message": message}
        return {"success": False, "error": f"未知的重构策略：{strategy}"}
    
    def explain_code(self, source_code: str, detail_level: str = "brief"):
        """解释代码功能"""
        structure = self.get_code_structure(source_code)
        metrics = self.get_code_metrics(source_code)
        
        explanation = {
            "summary": f"这段代码包含 {len(structure.get('functions', []))} 个函数 "
                      f"和 {len(structure.get('classes', []))} 个类",
            "imports": structure.get("imports", []),
            "functions": [
                {"name": f["name"], "args": f["args"], "docstring": f.get("docstring")}
                for f in structure.get("functions", [])
            ],
            "classes": [
                {"name": c["name"], "bases": c.get("bases", []), "methods": c.get("methods", [])}
                for c in structure.get("classes", [])
            ],
            "metrics": metrics
        }
        
        if detail_level == "detailed":
            explanation["issues"] = self.review_code(source_code).get("issues", [])
        
        return explanation


__all__ = ['CodeAnalyzer', 'CodeGenerator', 'CodeReviewer', 'CodeEngine']
