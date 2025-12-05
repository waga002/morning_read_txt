#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本功能：将type为textbook_review，而内容实际上是古诗词的，增加"alignment": "0"
判断标准：
1. type为"textbook_review"
2. dynasty不为空且不是"现代"
3. 内容像古诗词（短句、有标点）
"""

import json
import os
import glob

def is_poem_like(content_obj):
    """
    判断内容是否像古诗词
    特征：短句、有标点（，。；等）
    """
    if not content_obj or not isinstance(content_obj, list):
        return False
    
    for content_item in content_obj:
        if isinstance(content_item, dict) and 'text' in content_item:
            text = content_item['text']
            # 古诗词特征：短句（通常不超过30字）、有标点
            if len(text) < 30 and ('，' in text or '。' in text or '；' in text or '：' in text):
                return True
        elif isinstance(content_item, str):
            if len(content_item) < 30 and ('，' in content_item or '。' in content_item):
                return True
    
    return False

def is_ancient_dynasty(dynasty):
    """
    判断是否是古代朝代（不是现代）
    """
    if not dynasty or dynasty == '':
        return False
    
    modern_keywords = ['现代', '当代', '今']
    return dynasty not in modern_keywords

def process_json_file(file_path):
    """
    处理单个JSON文件，为符合条件的项目添加"alignment": "0"
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
            # 检查是否符合条件
            if item.get('type') == 'textbook_review':
                dynasty = item.get('dynasty', '')
                content_obj = item.get('contentObject', [])
                
                # 判断是否是古诗词
                if is_ancient_dynasty(dynasty) and is_poem_like(content_obj):
                    # 如果还没有alignment字段，或者alignment不是"0"
                    if 'alignment' not in item:
                        item['alignment'] = "0"
                        modified_count[0] += 1
                    elif item.get('alignment') != "0":
                        item['alignment'] = "0"
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
    
    print(f"完成！共修改了 {modified_count[0]} 个alignment字段。\n")
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
    print(f"共处理 {total_files} 个文件，总共修改了 {total_modified} 个alignment字段。")

if __name__ == "__main__":
    main()

