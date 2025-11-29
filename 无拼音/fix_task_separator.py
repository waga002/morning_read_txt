#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本功能：移除task字段中的"！！"和"!!"分隔符
例如："task": "问题1。！！问题2？" 修改为 "task": "问题1。问题2？"
"""

import json
import os
import glob
import re

def process_json_file(file_path):
    """
    处理单个JSON文件，移除task字段中的"！！"和"!!"
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
            # 如果包含task字段，移除其中的"！！"和"!!"
            if 'task' in item and isinstance(item['task'], str):
                original = item['task']
                new_value = original
                
                # 移除"！！"和"!!"
                if '！！' in new_value or '!!' in new_value:
                    new_value = new_value.replace('！！', '')
                    new_value = new_value.replace('!!', '')
                    # 清理可能出现的多余空格
                    new_value = re.sub(r'\s+', ' ', new_value).strip()
                    
                    if new_value != original:
                        item['task'] = new_value
                        modified_count[0] += 1
            
            # 递归处理所有值
            for key, value in item.items():
                process_item(value)
        elif isinstance(item, list):
            # 递归处理列表中的每个元素
            for element in item:
                process_item(element)
    
    # 处理数据
    process_item(data)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent='\t')
    
    print(f"完成！共修改了 {modified_count[0]} 个task字段。\n")
    return modified_count[0]

def process_text_file(file_path):
    """
    使用文本方式处理文件（当JSON解析失败时）
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计修改数量
    modified_count = 0
    
    # 匹配task字段并替换
    def replace_in_task(match):
        nonlocal modified_count
        full_match = match.group(0)
        task_value = match.group(1)
        
        if '！！' in task_value or '!!' in task_value:
            new_value = task_value.replace('！！', '').replace('!!', '')
            new_value = re.sub(r'\s+', ' ', new_value).strip()
            modified_count += 1
            return f'"task": "{new_value}"'
        
        return full_match
    
    pattern = r'"task":\s*"([^"]*(?:\\.[^"]*)*)"'
    content = re.sub(pattern, replace_in_task, content)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"完成！共修改了 {modified_count} 个task字段。\n")
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
    print(f"共处理 {total_files} 个文件，总共修改了 {total_modified} 个task字段。")

if __name__ == "__main__":
    main()

