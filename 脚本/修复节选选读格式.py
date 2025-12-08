#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复标题格式：将"（节选，xxx）"替换为"（节选·xxx）"
将"（选读，xxx）"替换为"（选读·xxx）"
"""
import json
import re
from pathlib import Path

def fix_title_format(data, file_path):
    """修复标题格式"""
    fixed_count = 0
    modified = False
    
    for week_data in data:
        for content_item in week_data.get('content', []):
            # 修复title字段
            title = content_item.get('title', '')
            if title:
                original_title = title
                
                # 替换"（节选，"为"（节选·"
                if '（节选，' in title:
                    title = title.replace('（节选，', '（节选·')
                    fixed_count += 1
                    modified = True
                
                # 替换"（选读，"为"（选读·"
                if '（选读，' in title:
                    title = title.replace('（选读，', '（选读·')
                    fixed_count += 1
                    modified = True
                
                # 如果标题被修改，更新
                if title != original_title:
                    content_item['title'] = title
                    print(f"修复: {file_path.name}")
                    print(f"  原标题: {original_title}")
                    print(f"  新标题: {title}")
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
                
                fixed_count, modified = fix_title_format(data, txt_file)
                
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
                
                fixed_count, modified = fix_title_format(data, txt_file)
                
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
    print(f"总计修复 {total_fixed} 处标题格式")
    print(f"修改了 {len(files_modified)} 个文件:")
    for filename in files_modified:
        print(f"  - {filename}")

if __name__ == "__main__":
    print("开始修复标题格式...")
    print("=" * 80)
    fix_all_files()

