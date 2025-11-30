#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计1-6年级所有类型为ancient_poem的文章
统计总数和去重后的数量
"""

import json
import os
from collections import defaultdict

def extract_poem_text(content_object):
    """
    提取古诗词文本内容
    """
    if not content_object:
        return ""
    
    lines = []
    for item in content_object:
        if isinstance(item, dict):
            text = item.get('text', '')
            if text:
                lines.append(text)
        elif isinstance(item, str):
            if item:
                lines.append(item)
    
    return '\n'.join(lines)

def process_file(file_path, all_poems, unique_poems):
    """
    处理单个文件，提取ancient_poem类型的文章
    all_poems: 所有文章列表（不去重）
    unique_poems: 去重后的文章字典
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return
    
    # 递归处理JSON数据
    def process_item(item, grade=None, term=None, week=None, day=None, theme=None):
        if isinstance(item, dict):
            # 更新上下文信息
            if 'grade' in item:
                grade = item.get('grade')
            if 'term' in item:
                term = item.get('term')
            if 'week' in item:
                week = item.get('week')
            if 'day' in item:
                day = item.get('day')
            if 'theme' in item:
                theme = item.get('theme')
            
            # 检查是否是ancient_poem类型
            if item.get('type') == 'ancient_poem':
                title = item.get('title', '')
                author = item.get('author', '')
                dynasty = item.get('dynasty', '')
                content_object = item.get('contentObject', [])
                annotation = item.get('annotation', '')
                translation = item.get('translation', '')
                
                poem_text = extract_poem_text(content_object)
                
                # 记录所有文章（不去重）
                poem_info = {
                    'title': title,
                    'author': author,
                    'dynasty': dynasty,
                    'text': poem_text,
                    'annotation': annotation,
                    'translation': translation,
                    'grade': grade,
                    'term': term,
                    'week': week,
                    'day': day,
                    'theme': theme,
                    'file': os.path.basename(file_path)
                }
                all_poems.append(poem_info)
                
                # 创建唯一标识（用于去重）
                # 使用标题+作者+朝代+内容前100字符作为唯一标识
                poem_key = f"{title}|{author}|{dynasty}|{poem_text[:100]}"
                
                # 如果还没有记录，添加到去重字典
                if poem_key not in unique_poems:
                    unique_poems[poem_key] = {
                        'title': title,
                        'author': author,
                        'dynasty': dynasty,
                        'text': poem_text,
                        'annotation': annotation,
                        'translation': translation,
                        'locations': []  # 记录出现的位置
                    }
                
                # 记录出现位置
                location = {
                    'grade': grade,
                    'term': term,
                    'week': week,
                    'day': day,
                    'theme': theme,
                    'file': os.path.basename(file_path)
                }
                unique_poems[poem_key]['locations'].append(location)
            
            # 递归处理所有值
            for key, value in item.items():
                process_item(value, grade, term, week, day, theme)
        elif isinstance(item, list):
            for element in item:
                process_item(element, grade, term, week, day, theme)
    
    process_item(data)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    all_poems = []  # 所有文章（不去重）
    unique_poems = {}  # 去重后的文章
    
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
                    process_file(file_path, all_poems, unique_poems)
    
    # 统计结果
    total_count = len(all_poems)
    unique_count = len(unique_poems)
    
    print("\n" + "=" * 80)
    print("统计结果")
    print("=" * 80)
    print(f"类型为 ancient_poem 的文章总数（不去重）：{total_count} 篇")
    print(f"类型为 ancient_poem 的文章去重后数量：{unique_count} 篇")
    print(f"重复出现的文章数量：{total_count - unique_count} 篇")
    print("=" * 80)
    
    # 按朝代统计（去重后）
    stats = defaultdict(int)
    for poem in unique_poems.values():
        dynasty = poem['dynasty'] or '无朝代'
        stats[dynasty] += 1
    
    print("\n按朝代统计（去重后）：")
    for dynasty, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {dynasty}: {count} 篇")
    
    # 找出重复出现的文章
    print("\n重复出现的文章（出现次数>1）：")
    repeated_count = 0
    for poem_key, poem_info in unique_poems.items():
        if len(poem_info['locations']) > 1:
            repeated_count += 1
            print(f"\n  {poem_info['title']} - {poem_info['author']} ({poem_info['dynasty']})")
            print(f"    出现 {len(poem_info['locations'])} 次")
            locations_str = "、".join([f"{loc['file']}" for loc in poem_info['locations'][:5]])
            if len(poem_info['locations']) > 5:
                locations_str += f"等{len(poem_info['locations'])}处"
            print(f"    位置：{locations_str}")
    
    print(f"\n共有 {repeated_count} 篇文章出现多次")

if __name__ == '__main__':
    main()

