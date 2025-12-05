#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查1-6年级所有文件中的type字段，找出不符合定义的类型
"""

import json
import os
from collections import defaultdict

# 定义合法的type类型
VALID_TYPES = {
    'textbook_review',
    'children_poem',
    'ancient_poem',
    'classics',
    'story_legend',
    'modern_prose',
    'classical_chinese',
    'daily_accumulation',
    'fun_riddles',
    'tongue_twisters'
}

def find_all_types(file_path):
    """
    找出文件中所有的type值
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return []
    
    types_found = []
    
    def process_item(item, path=""):
        if isinstance(item, dict):
            # 检查是否有type字段
            if 'type' in item:
                type_value = item.get('type', '')
                title = item.get('title', '')
                author = item.get('author', '')
                dynasty = item.get('dynasty', '')
                
                types_found.append({
                    'type': type_value,
                    'title': title,
                    'author': author,
                    'dynasty': dynasty,
                    'file': os.path.basename(file_path),
                    'path': path
                })
            
            # 递归处理所有值
            for key, value in item.items():
                new_path = f"{path}.{key}" if path else key
                process_item(value, new_path)
        elif isinstance(item, list):
            for i, element in enumerate(item):
                new_path = f"{path}[{i}]" if path else f"[{i}]"
                process_item(element, new_path)
    
    process_item(data)
    return types_found

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    all_types = []
    invalid_types = defaultdict(list)
    
    # 处理有拼音和无拼音两个目录
    for subdir in ['有拼音', '无拼音']:
        subdir_path = os.path.join(base_dir, subdir)
        if not os.path.exists(subdir_path):
            continue
        
        print(f"正在检查目录: {subdir}")
        
        # 遍历1-6年级
        for grade in range(1, 7):
            grade_dir = os.path.join(subdir_path, f"{grade}年级")
            if not os.path.exists(grade_dir):
                continue
            
            print(f"  检查 {grade}年级...")
            
            # 遍历所有单元文件
            for filename in os.listdir(grade_dir):
                if filename.endswith('.txt') and '汇总表' not in filename:
                    file_path = os.path.join(grade_dir, filename)
                    types_in_file = find_all_types(file_path)
                    all_types.extend(types_in_file)
                    
                    # 检查是否有无效类型
                    for type_info in types_in_file:
                        if type_info['type'] not in VALID_TYPES:
                            invalid_types[type_info['type']].append(type_info)
    
    # 统计所有类型
    type_stats = defaultdict(int)
    for type_info in all_types:
        type_stats[type_info['type']] += 1
    
    print("\n" + "=" * 80)
    print("所有type类型统计：")
    print("=" * 80)
    for type_name, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
        status = "✓" if type_name in VALID_TYPES else "✗"
        print(f"  {status} {type_name}: {count} 个")
    
    # 显示无效类型
    if invalid_types:
        print("\n" + "=" * 80)
        print("发现无效的type类型：")
        print("=" * 80)
        for invalid_type, items in invalid_types.items():
            print(f"\n无效类型: '{invalid_type}' (出现 {len(items)} 次)")
            print("详细信息：")
            for item in items:
                print(f"  文件: {item['file']}")
                print(f"  标题: {item['title']}")
                print(f"  作者: {item.get('author', '无')}")
                print(f"  朝代: {item.get('dynasty', '无')}")
                print()
    else:
        print("\n✓ 所有type类型都是有效的！")
    
    return invalid_types

if __name__ == '__main__':
    main()

