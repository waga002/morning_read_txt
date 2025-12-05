#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正1-6年级所有文件中不符合定义的type字段
"""

import json
import os

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

# 定义类型映射规则
TYPE_MAPPING = {
    'classic_recitation': 'classics',  # 经典诵读 -> 国学经典
    'maxim_proverb': 'daily_accumulation',  # 格言谚语 -> 日积月累
    'wise_saying': 'daily_accumulation',  # 智慧小口诀 -> 日积月累
    'saying_proverb': 'daily_accumulation',  # 谚语 -> 日积月累
    'proverb_saying': 'daily_accumulation',  # 谚语 -> 日积月累
    'folk_proverb': 'daily_accumulation',  # 民间谚语 -> 日积月累
    'childrens_verse': 'children_poem',  # 童诗 -> 童谣童诗
}

def fix_type_in_file(file_path):
    """
    修正文件中的type字段
    返回修正的数量
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return 0
    
    fixed_count = [0]
    
    def process_item(item):
        if isinstance(item, dict):
            # 检查并修正type字段
            if 'type' in item:
                old_type = item.get('type', '')
                if old_type in TYPE_MAPPING:
                    new_type = TYPE_MAPPING[old_type]
                    item['type'] = new_type
                    fixed_count[0] += 1
                    title = item.get('title', '')
                    print(f"    修正: '{old_type}' -> '{new_type}' (标题: {title})")
                elif old_type not in VALID_TYPES:
                    # 如果不在映射表中也不在有效类型中，尝试根据内容判断
                    title = item.get('title', '')
                    author = item.get('author', '')
                    dynasty = item.get('dynasty', '')
                    
                    # 根据内容特征判断类型
                    if '口诀' in title or '谚语' in title or '格言' in title:
                        item['type'] = 'daily_accumulation'
                        fixed_count[0] += 1
                        print(f"    修正: '{old_type}' -> 'daily_accumulation' (标题: {title})")
                    elif dynasty and dynasty != '现代' and dynasty != '':
                        # 有朝代信息，可能是classics
                        if '弟子规' in title or '三字经' in title or '论语' in title:
                            item['type'] = 'classics'
                            fixed_count[0] += 1
                            print(f"    修正: '{old_type}' -> 'classics' (标题: {title})")
                    else:
                        print(f"    警告: 无法确定类型 '{old_type}' (标题: {title})")
            
            # 递归处理所有值
            for key, value in item.items():
                process_item(value)
        elif isinstance(item, list):
            for element in item:
                process_item(element)
    
    process_item(data)
    
    # 如果有修正，写回文件
    if fixed_count[0] > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent='\t')
    
    return fixed_count[0]

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    total_fixed = 0
    files_fixed = 0
    
    # 处理有拼音和无拼音两个目录
    for subdir in ['有拼音', '无拼音']:
        subdir_path = os.path.join(base_dir, subdir)
        if not os.path.exists(subdir_path):
            continue
        
        print(f"正在处理目录: {subdir}")
        
        # 遍历1-6年级
        for grade in range(1, 7):
            grade_dir = os.path.join(subdir_path, f"{grade}年级")
            if not os.path.exists(grade_dir):
                continue
            
            print(f"  处理 {grade}年级...")
            
            # 遍历所有单元文件
            for filename in os.listdir(grade_dir):
                if filename.endswith('.txt') and '汇总表' not in filename:
                    file_path = os.path.join(grade_dir, filename)
                    fixed = fix_type_in_file(file_path)
                    if fixed > 0:
                        files_fixed += 1
                        total_fixed += fixed
                        print(f"    文件 {filename}: 修正了 {fixed} 个type字段")
    
    print("\n" + "=" * 80)
    print("修正完成！")
    print("=" * 80)
    print(f"共修正了 {total_fixed} 个type字段")
    print(f"涉及 {files_fixed} 个文件")

if __name__ == '__main__':
    main()

