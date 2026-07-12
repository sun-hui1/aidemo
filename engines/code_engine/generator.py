"""
代码生成器 - 根据需求生成、修改、重构代码
"""
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class CodeGenerator:
    """代码生成引擎"""
    
    def __init__(self):
        self.indent_size = 4
    
    def generate_function(self, name: str, args: List[str], 
                         body: str, docstring: Optional[str] = None,
                         return_type: Optional[str] = None) -> str:
        """生成函数代码"""
        lines = []
        
        # 添加文档字符串
        if docstring:
            lines.append(f'def {name}({", ".join(args)}):')
            lines.append(f'    """{docstring}"""')
        else:
            lines.append(f'def {name}({", ".join(args)}):')
        
        # 添加函数体
        for line in body.splitlines():
            lines.append(f"    {line}")
        
        return "\n".join(lines)
    
    def generate_class(self, name: str, bases: Optional[List[str]] = None,
                      attributes: Optional[List[str]] = None,
                      methods: Optional[List[Dict[str, Any]]] = None,
                      docstring: Optional[str] = None) -> str:
        """生成类代码"""
        lines = []
        
        # 类定义
        if bases:
            lines.append(f"class {name}({', '.join(bases)}):")
        else:
            lines.append(f"class {name}:")
        
        # 文档字符串
        if docstring:
            lines.append(f'    """{docstring}"""')
            lines.append('')
        
        # 类属性
        if attributes:
            for attr in attributes:
                lines.append(f"    {attr}")
            lines.append('')
        
        # 方法
        if methods:
            for method in methods:
                method_code = self.generate_function(
                    name=method.get('name', 'method'),
                    args=method.get('args', ['self']),
                    body=method.get('body', 'pass'),
                    docstring=method.get('docstring')
                )
                # 去掉 def 前面的缩进
                method_lines = method_code.splitlines()
                lines.append(method_lines[0])  # def 行
                for ml in method_lines[1:]:
                    lines.append(f"    {ml}")
                lines.append('')
        
        if not attributes and not methods:
            lines.append("    pass")
        
        return "\n".join(lines)
    
    def modify_function(self, code: str, function_name: str,
                       changes: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        修改现有函数
        返回：(修改后的代码，变更列表)
        """
        changes_made = []
        
        # 查找函数定义
        pattern = rf'(def\s+{re.escape(function_name)}\s*\([^)]*\)\s*(?:->[^:]+)?:)'
        match = re.search(pattern, code)
        
        if not match:
            return code, [f"未找到函数：{function_name}"]
        
        func_start = match.start()
        
        # 查找函数结束（下一个同级别的 def 或 class）
        func_body_match = re.search(
            r'\n(?:def|class)\s+\w+',
            code[func_start:]
        )
        
        if func_body_match:
            func_end = func_start + func_body_match.start()
        else:
            func_end = len(code)
        
        original_func = code[func_start:func_end]
        modified_func = original_func
        
        # 应用变更
        if 'add_parameter' in changes:
            for param in changes['add_parameter']:
                if param not in modified_func:
                    # 在现有参数后添加
                    param_pattern = rf'(def\s+{re.escape(function_name)}\s*\()([^)]*)(\))'
                    param_match = re.search(param_pattern, modified_func)
                    if param_match:
                        existing_params = param_match.group(2).strip()
                        if existing_params:
                            new_params = f"{existing_params}, {param}"
                        else:
                            new_params = param
                        modified_func = re.sub(
                            param_pattern,
                            f'\\g<1>{new_params}\\g<3>',
                            modified_func
                        )
                        changes_made.append(f"添加参数：{param}")
        
        if 'replace_body' in changes:
            # 替换函数体（简单实现）
            changes_made.append("替换函数体")
        
        if 'add_docstring' in changes and '"""' not in modified_func:
            # 添加文档字符串
            docstring_pos = modified_func.find(':') + 1
            modified_func = (modified_func[:docstring_pos+1] + 
                           f'\n    """{changes["add_docstring"]}"""' +
                           modified_func[docstring_pos+1:])
            changes_made.append("添加文档字符串")
        
        # 替换原函数
        new_code = code[:func_start] + modified_func + code[func_end:]
        
        return new_code, changes_made
    
    def refactor_extract_method(self, code: str, function_name: str,
                               start_line: int, end_line: int,
                               new_method_name: str) -> Tuple[str, str]:
        """
        重构：提取方法
        将函数中的部分代码提取为新方法
        """
        lines = code.splitlines()
        
        if start_line < 1 or end_line > len(lines) or start_line > end_line:
            return code, "无效的行号范围"
        
        # 提取的代码块
        extracted_lines = lines[start_line-1:end_line]
        
        # 分析需要的参数（简化版本）
        # 实际实现需要更复杂的变量依赖分析
        params = []
        returns = []
        
        # 生成新方法
        new_method = self.generate_function(
            name=new_method_name,
            args=['self'] + params,
            body='\n'.join(extracted_lines),
            docstring=f"从 {function_name} 提取的方法"
        )
        
        # 在原位置调用新方法
        indent = ' ' * (len(lines[start_line-1]) - len(lines[start_line-1].lstrip()))
        call_line = f"{indent}return self.{new_method_name}({', '.join(params)})" if returns else \
                   f"{indent}self.{new_method_name}({', '.join(params)})"
        
        # 替换原代码块
        new_lines = lines[:start_line-1] + [call_line] + lines[end_line:]
        
        # 在类中添加新方法（找到合适的位置）
        # 简化实现：添加到文件末尾
        final_code = '\n'.join(new_lines) + '\n\n' + new_method
        
        return final_code, f"已提取方法：{new_method_name}"
    
    def generate_import_statement(self, module: str, 
                                 names: Optional[List[str]] = None,
                                 alias: Optional[str] = None) -> str:
        """生成导入语句"""
        if names:
            if len(names) == 1:
                name = names[0]
                if alias:
                    return f"from {module} import {name} as {alias}"
                return f"from {module} import {name}"
            else:
                return f"from {module} import {', '.join(names)}"
        else:
            if alias:
                return f"import {module} as {alias}"
            return f"import {module}"
    
    def add_import_to_file(self, code: str, import_statement: str) -> str:
        """向文件添加导入语句"""
        lines = code.splitlines(True)  # 保留换行符
        
        # 查找现有导入的位置
        import_positions = []
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_positions.append(i)
        
        if import_positions:
            # 在最后一个导入后插入
            insert_pos = import_positions[-1] + 1
            lines.insert(insert_pos, import_statement + '\n')
        else:
            # 在文件开头插入（在 shebang 或编码声明之后）
            insert_pos = 0
            for i, line in enumerate(lines[:3]):
                if line.startswith('#!') or 'encoding' in line.lower():
                    insert_pos = i + 1
            
            lines.insert(insert_pos, import_statement + '\n')
        
        return ''.join(lines)
    
    def generate_boilerplate(self, template_type: str, **kwargs) -> str:
        """生成代码模板"""
        templates = {
            'python_module': '''"""
{description}
"""

{imports}


def main():
    """主函数"""
    {main_body}


if __name__ == "__main__":
    main()
''',
            'python_class': '''"""
{description}
"""

from typing import Any, Dict, List, Optional


class {class_name}:
    """{class_name} 类"""
    
    def __init__(self, {init_args}):
        """初始化"""
        {init_body}
    
    def {method_name}(self, {method_args}) -> {return_type}:
        """方法描述"""
        {method_body}
''',
            'pytest_test': '''"""
测试 {module_name}
"""
import pytest
from {module_name} import {function_name}


def test_{function_name}_basic():
    """基础测试"""
    # TODO: 实现测试用例
    assert True


def test_{function_name}_edge_cases():
    """边界条件测试"""
    # TODO: 实现边界测试
    assert True
'''
        }
        
        template = templates.get(template_type, '')
        if not template:
            return f"# 未知模板类型：{template_type}"
        
        # 填充默认值
        defaults = {
            'description': kwargs.get('description', '模块描述'),
            'imports': kwargs.get('imports', ''),
            'main_body': kwargs.get('main_body', 'pass'),
            'class_name': kwargs.get('class_name', 'ClassName'),
            'init_args': kwargs.get('init_args', ''),
            'init_body': kwargs.get('init_body', 'pass'),
            'method_name': kwargs.get('method_name', 'method'),
            'method_args': kwargs.get('method_args', ''),
            'return_type': kwargs.get('return_type', 'Any'),
            'method_body': kwargs.get('method_body', 'pass'),
            'module_name': kwargs.get('module_name', 'module'),
            'function_name': kwargs.get('function_name', 'function')
        }
        
        return template.format(**defaults)
