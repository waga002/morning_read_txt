#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本功能：对于type为classics的文章，按照"；"和"。"拆开contentObject中的text字段
例如：
"text": "惟德学，惟才艺；不如人，当自砺。"
拆成：
"text": "惟德学，惟才艺；"
"text": "不如人，当自砺。"
"""

import json
import os
import glob
import re

def split_text_by_punctuation(text):
    """
    按照"；"和"。"拆分文本，保留分隔符
    例如："惟德学，惟才艺；不如人，当自砺。" 
    拆成：["惟德学，惟才艺；", "不如人，当自砺。"]
    """
    if not text:
        return []
    
    parts = []
    current = ""
    
    for char in text:
        current += char
        if char in ['；', '。']:
            if current.strip():
                parts.append(current.strip())
            current = ""
    
    # 处理最后剩余的部分（如果没有以"；"或"。"结尾）
    if current.strip():
        parts.append(current.strip())
    
    return parts

def process_json_file(file_path):
    """
    处理单个JSON文件，拆分classics类型的text字段
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
            # 如果type为classics，处理contentObject
            if item.get('type') == 'classics':
                content_obj = item.get('contentObject', [])
                if isinstance(content_obj, list):
                    new_content_obj = []
                    for content_item in content_obj:
                        if isinstance(content_item, dict) and 'text' in content_item:
                            text = content_item['text']
                            # 按照"；"和"。"拆分
                            parts = split_text_by_punctuation(text)
                            
                            if len(parts) > 1:
                                # 如果拆分成多个部分，创建多个text对象
                                for part in parts:
                                    new_content_obj.append({"text": part})
                                modified_count[0] += 1
                            else:
                                # 如果不需要拆分，保留原样
                                new_content_obj.append(content_item)
                        else:
                            # 保留其他字段
                            new_content_obj.append(content_item)
                    
                    item['contentObject'] = new_content_obj
            
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
    
    print(f"完成！共修改了 {modified_count[0]} 个text字段。\n")
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
    print(f"共处理 {total_files} 个文件，总共修改了 {total_modified} 个text字段。")

if __name__ == "__main__":
    main()

