#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本功能：将JSON文件中不正确的作者信息替换为空字符串
例如："author": "民间传说" 修改为 "author": ""
例如："author": "《山海经》" 修改为 "author": ""
"""

import json
import os
import glob
import re

def should_replace_author(author_value):
    """
    判断author字段是否应该被替换为空字符串
    包括：
    1. "民间传说"
    2. 以《开头并以》结尾的（包括带"改编"的）
    3. "根据...改编" 或 "根据...整理" 等实际为出处的
    """
    if not isinstance(author_value, str):
        return False
    
    # 处理"民间传说"
    if author_value == "民间传说":
        return True
    
    # 处理以《开头并以》结尾的（包括带"改编"的）
    # 匹配模式：以《开头，以》结尾，中间可能有任何字符，后面可能还有"改编"等
    if re.match(r'^《.*》', author_value):
        return True
    
    # 处理"根据...改编"、"根据...整理"等实际为出处的
    if re.match(r'^根据.*(改编|整理)', author_value):
        return True
    
    return False

def process_json_file(file_path):
    """
    处理单个JSON文件，将不正确的作者信息替换为"author": ""
    包括："民间传说" 和 以《开头并以》结尾的（如"《山海经》"）
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
            # 如果包含author字段且应该被替换，则替换为空字符串
            if 'author' in item and isinstance(item['author'], str):
                if should_replace_author(item['author']):
                    item['author'] = ""
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
    
    print(f"完成！共修改了 {modified_count[0]} 个author字段。\n")
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
    print(f"共处理 {total_files} 个文件，总共修改了 {total_modified} 个author字段。")

if __name__ == "__main__":
    main()

