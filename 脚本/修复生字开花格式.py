#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复"生字开花"格式：将"→"替换为"--"
例如：天 → 天空  →  天-- 天空
"""
import json
import os
import re
from pathlib import Path

def fix_shengzi_kaihua_format(data, file_path):
    """修复生字开花格式"""
    fixed_count = 0
    modified = False
    
    for week_data in data:
        for content_item in week_data.get('content', []):
            # 检查contentObject中是否有"生字开花"
            for obj in content_item.get('contentObject', []):
                if isinstance(obj, dict):
                    # 检查title是否为"生字开花"
                    obj_title = obj.get('title', '')
                    if '生字开花' in obj_title:
                        # 检查content数组
                        if 'content' in obj:
                            for sub_item in obj.get('content', []):
                                if isinstance(sub_item, dict) and 'text' in sub_item:
                                    text = sub_item['text']
                                    # 检查是否包含"→"
                                    if '→' in text:
                                        # 替换"→"为"--"
                                        new_text = text.replace('→', '--')
                                        sub_item['text'] = new_text
                                        fixed_count += 1
                                        modified = True
                                        print(f"修复: {file_path.name}")
                                        print(f"  原文本: {text}")
                                        print(f"  新文本: {new_text}")
                                        print()
    
    return fixed_count, modified

def fix_all_files():
    """修复所有文件"""
    base_dir = Path(__file__).parent
    
    # 检查有拼音的1年级和2年级文件
    total_fixed = 0
    files_modified = []
    
    for grade in [1, 2]:
        grade_dir = base_dir / "有拼音" / f"{grade}年级"
        if not grade_dir.exists():
            continue
        
        txt_files = sorted(grade_dir.glob("*.txt"))
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                fixed_count, modified = fix_shengzi_kaihua_format(data, txt_file)
                
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
    print(f"总计修复 {total_fixed} 处生字开花格式")
    print(f"修改了 {len(files_modified)} 个文件:")
    for filename in files_modified:
        print(f"  - {filename}")

if __name__ == "__main__":
    print("开始修复生字开花格式...")
    print("=" * 80)
    fix_all_files()

