#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本功能：将JSON文件中translation字段里包含"无需翻译"的内容替换为空字符串
例如："translation": "（白话故事，无需翻译）" 修改为 "translation": ""
"""

import json
import os
import glob
import re

def should_replace_translation(translation_value):
    """
    判断translation字段是否应该被替换为空字符串
    包括所有包含"无需翻译"的内容
    """
    if not isinstance(translation_value, str):
        return False
    
    # 处理包含"无需翻译"的内容
    if "无需翻译" in translation_value:
        return True
    
    return False

def process_json_file(file_path):
    """
    处理单个JSON文件，将包含"无需翻译"的translation字段替换为"translation": ""
    """
    print(f"正在处理文件: {file_path}")
    
    # 读取文件
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  JSON解析错误: {e}")
        print(f"  跳过此文件\n")
        return 0
    
    # 统计修改数量
    modified_count = [0]
    
    # 递归处理JSON数据结构
    def process_item(item):
        if isinstance(item, dict):
            # 如果包含translation字段且应该被替换，则替换为空字符串
            if 'translation' in item and isinstance(item['translation'], str):
                if should_replace_translation(item['translation']):
                    item['translation'] = ""
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
    
    print(f"完成！共修改了 {modified_count[0]} 个translation字段。\n")
    return modified_count[0]

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
    print(f"共处理 {total_files} 个文件，总共修改了 {total_modified} 个translation字段。")

if __name__ == "__main__":
    main()

