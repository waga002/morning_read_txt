#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本功能：将JSON文件中annotation字段为"（无难点）"的内容替换为空字符串
例如："annotation": "（无难点）" 修改为 "annotation": ""
"""

import json
import os
import glob
import re

def process_json_file(file_path):
    """
    处理单个JSON文件，将annotation字段为"（无难点）"的替换为空字符串
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
            # 如果包含annotation字段，处理"（无难点）"
            if 'annotation' in item and isinstance(item['annotation'], str):
                original = item['annotation']
                new_value = original
                
                # 情况1：整个annotation就是"（无难点）"
                if original == "（无难点）":
                    new_value = ""
                    modified_count[0] += 1
                # 情况2：annotation中包含"（无难点）"作为注释的一部分
                elif "（无难点）" in original:
                    # 删除"（无难点）"及其前面的分隔符
                    # 处理 "。！！（无难点）" 或 "！！（无难点）" 的情况
                    new_value = re.sub(r'。*！！（无难点）', '', original)
                    new_value = re.sub(r'！！（无难点）', '', new_value)
                    new_value = re.sub(r'（无难点）', '', new_value)
                    # 清理末尾可能的多余分隔符
                    new_value = re.sub(r'！！$', '', new_value)
                    new_value = re.sub(r'。$', '', new_value)
                    if new_value != original:
                        modified_count[0] += 1
                
                item['annotation'] = new_value
            
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
    
    print(f"完成！共修改了 {modified_count[0]} 个annotation字段。\n")
    return modified_count[0]

def process_text_file(file_path):
    """
    使用文本方式处理文件（当JSON解析失败时）
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计修改数量
    modified_count = 0
    
    # 情况1：匹配 "annotation": "（无难点）"
    pattern1 = r'"annotation":\s*"（无难点）"'
    matches1 = re.findall(pattern1, content)
    if matches1:
        content = re.sub(pattern1, '"annotation": ""', content)
        modified_count += len(matches1)
    
    # 情况2：匹配annotation中包含"（无难点）"的情况
    def replace_in_annotation(match):
        nonlocal modified_count
        full_match = match.group(0)
        annotation_value = match.group(1)
        
        if "（无难点）" in annotation_value:
            # 删除"（无难点）"及其前面的分隔符
            new_value = re.sub(r'。*！！（无难点）', '', annotation_value)
            new_value = re.sub(r'！！（无难点）', '', new_value)
            new_value = re.sub(r'（无难点）', '', new_value)
            # 清理末尾可能的多余分隔符
            new_value = re.sub(r'！！$', '', new_value)
            new_value = re.sub(r'。$', '', new_value)
            
            if new_value != annotation_value:
                modified_count += 1
                return f'"annotation": "{new_value}"'
        
        return full_match
    
    pattern2 = r'"annotation":\s*"([^"]*(?:\\.[^"]*)*)"'
    content = re.sub(pattern2, replace_in_annotation, content)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"完成！共修改了 {modified_count} 个annotation字段。\n")
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
    print(f"共处理 {total_files} 个文件，总共修改了 {total_modified} 个annotation字段。")

if __name__ == "__main__":
    main()

