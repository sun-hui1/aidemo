#!/usr/bin/env python3
"""示例代码文件 - 用于演示代码审查功能"""

import os
import sys

# 全局变量
DEBUG = True
API_KEY = "sk-1234567890abcdef"  # 硬编码的敏感信息

def process_data(data):
    x = data
    y = x * 2
    z = y + 10
    if z > 100:
        if z > 200:
            if z > 300:
                return z * 2
            else:
                return z
        else:
            return y
    else:
        return x

def calculate(a,b,c,d,e,f,g,h):
    """计算函数 - 参数过多"""
    result = a + b + c + d + e + f + g + h
    return result

def unsafe_eval(user_input):
    """危险的 eval 使用"""
    return eval(user_input)

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self, items):
        for item in items:
            self.data.append(item)
        return self.data

# 主程序
if __name__ == '__main__':
    print("开始处理...")
    processor = DataProcessor()
    result = processor.process([1, 2, 3])
    print(f"结果：{result}")
