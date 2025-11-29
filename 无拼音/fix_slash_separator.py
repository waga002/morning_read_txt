#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本功能：将JSON文件中用"/"连接的文本替换为用" | "连接
例如："八字成语/名言" 修改为 "八字成语 | 名言"
例如："歇后语/谚语" 修改为 "歇后语 | 谚语"
"""

import json
import os
import glob
import re

def process_json_file(file_path):
    """
    处理单个JSON文件，将所有的"/"替换为" | "
    """
    print(f"正在处理文件: {file_path}")
    
    # 读取文件
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  JSON解析错误: {e}")
        print(f"  使用文本方式处理\n")
        return process_text_file(file_path)
    
    # 统计修改数量
    modified_count = [0]
    
    # 递归处理JSON数据结构
    def process_item(item):
        if isinstance(item, dict):
            # 处理所有字符串值
            for key, value in item.items():
                if isinstance(value, str) and '/' in value:
                    # 将"/"替换为" | "，但保留前后空格的处理
                    new_value = value.replace('/', ' | ')
                    if new_value != value:
                        item[key] = new_value
                        modified_count[0] += 1
                else:
                    process_item(value)
        elif isinstance(item, list):
            # 递归处理列表中的每个元素
            for element in item:
                process_item(element)
        elif isinstance(item, str) and '/' in item:
            # 这种情况不应该发生，因为字符串值应该在dict中处理
            pass
    
    # 处理数据
    process_item(data)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent='\t')
    
    print(f"完成！共修改了 {modified_count[0]} 处。\n")
    return modified_count[0]

def process_text_file(file_path):
    """
    使用文本方式处理文件（当JSON解析失败时）
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计修改数量
    original_count = content.count('/')
    
    # 替换所有的"/"为" | "
    # 但要注意，我们只替换字符串值中的"/"，不替换JSON结构中的
    # 使用正则表达式匹配字符串值中的"/"
    def replace_in_string(match):
        full_match = match.group(0)
        string_value = match.group(1)
        
        if '/' in string_value:
            new_value = string_value.replace('/', ' | ')
            return f'"{new_value}"'
        
        return full_match
    
    # 匹配字符串值
    pattern = r'"([^"]*(?:\\.[^"]*)*)"'
    content = re.sub(pattern, replace_in_string, content)
    
    new_count = content.count('/')
    modified_count = original_count - new_count
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"完成！共修改了约 {modified_count} 处。\n")
    return modified_count

def main():
    # 获取脚本所在目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 查找所有年级目录下的txt文件
    grade_dirs = ['3年级', '4年级', '5年级', '6年级']
    
    total_modified = 0
    total_files = 0
    
    for grade_dir in grade_dirs:
        grade_path = os.path.join(base_dir, grade_dir)
        if os.path.exists(grade_path):
            # 查找该目录下所有的txt文件
            txt_files = glob.glob(os.path.join(grade_path, '*.txt'))
            for file_path in sorted(txt_files):
                total_files += 1
                total_modified += process_json_file(file_path)
    
    print(f"所有文件处理完成！")
    print(f"共处理 {total_files} 个文件，总共修改了 {total_modified} 处。")

if __name__ == "__main__":
    main()

