#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复作者字段：将"author": "佚名"改为"author": ""
"""
import json
import os
import re
from pathlib import Path

def fix_author_yiming(data, file_path):
    """修复作者字段中的佚名"""
    fixed_count = 0
    modified = False
    
    for week_data in data:
        for content_item in week_data.get('content', []):
            # 检查author字段是否为"佚名"
            author = content_item.get('author', '')
            if author == '佚名':
                content_item['author'] = ''
                fixed_count += 1
                modified = True
                title = content_item.get('title', '')
                print(f"修复: {file_path.name}")
                print(f"  标题: {title}")
                print(f"  原作者: 佚名")
                print(f"  新作者: (空)")
                print()
    
    return fixed_count, modified

def fix_all_files():
    """修复所有文件"""
    base_dir = Path(__file__).parent
    
    # 检查所有年级的文件
    total_fixed = 0
    files_modified = []
    
    # 检查有拼音的1年级和2年级文件
    for grade in [1, 2]:
        grade_dir = base_dir / "有拼音" / f"{grade}年级"
        if not grade_dir.exists():
            continue
        
        txt_files = sorted(grade_dir.glob("*.txt"))
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                fixed_count, modified = fix_author_yiming(data, txt_file)
                
                if modified:
                    # 保存修改
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent='\t')
                    files_modified.append(txt_file.name)
                    total_fixed += fixed_count
                    print(f"已保存: {txt_file.name}\n")
            
            except Exception as e:
                print(f"处理文件 {txt_file.name} 时出错: {str(e)}\n")
    
    # 检查无拼音的3-6年级文件
    for grade in [3, 4, 5, 6]:
        grade_dir = base_dir / "无拼音" / f"{grade}年级"
        if not grade_dir.exists():
            continue
        
        txt_files = sorted(grade_dir.glob("*.txt"))
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                fixed_count, modified = fix_author_yiming(data, txt_file)
                
                if modified:
                    # 保存修改
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent='\t')
                    files_modified.append(txt_file.name)
                    total_fixed += fixed_count
                    print(f"已保存: {txt_file.name}\n")
            
            except Exception as e:
                print(f"处理文件 {txt_file.name} 时出错: {str(e)}\n")
    
    print("=" * 80)
    print("修复完成")
    print("=" * 80)
    print(f"总计修复 {total_fixed} 处作者字段")
    print(f"修改了 {len(files_modified)} 个文件:")
    for filename in files_modified:
        print(f"  - {filename}")

if __name__ == "__main__":
    print("开始修复作者字段...")
    print("=" * 80)
    fix_all_files()

