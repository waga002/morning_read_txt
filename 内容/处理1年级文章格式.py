#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理1年级所有文章的格式：
1. 只保留主标题，去掉括号内的内容，例如"三字经（选段）"改为"三字经"
2. 去掉所有的作者（author字段）
3. 去掉所有的朝代（dynasty字段）
"""
import json
import re
from pathlib import Path

def clean_title(title):
    """清理标题，去掉括号及其内容"""
    if not title:
        return title
    
    # 去掉中文括号及其内容
    title = re.sub(r'（[^）]*）', '', title)
    # 去掉英文括号及其内容
    title = re.sub(r'\([^)]*\)', '', title)
    
    return title.strip()

def process_grade1_files():
    """处理1年级所有文件"""
    base_dir = Path(__file__).parent
    grade1_dir = base_dir / "有拼音" / "1年级"
    
    if not grade1_dir.exists():
        print(f"错误：未找到1年级内容路径: {grade1_dir}")
        return
    
    total_modified = 0
    files_modified = []
    
    txt_files = sorted(grade1_dir.glob("*.txt"))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_modified = False
            
            for week_data in data:
                for content_item in week_data.get('content', []):
                    # 1. 处理标题
                    if 'title' in content_item:
                        original_title = content_item['title']
                        cleaned_title = clean_title(original_title)
                        if cleaned_title != original_title:
                            content_item['title'] = cleaned_title
                            file_modified = True
                            total_modified += 1
                            print(f"修改标题: {txt_file.name}")
                            print(f"  原标题: {original_title}")
                            print(f"  新标题: {cleaned_title}")
                            print()
                    
                    # 2. 删除author字段
                    if 'author' in content_item:
                        del content_item['author']
                        file_modified = True
                        total_modified += 1
                    
                    # 3. 删除dynasty字段
                    if 'dynasty' in content_item:
                        del content_item['dynasty']
                        file_modified = True
                        total_modified += 1
                    
                    # 4. 删除authorPinyin和dynastyPinyin字段（如果有）
                    if 'authorPinyin' in content_item:
                        del content_item['authorPinyin']
                        file_modified = True
                        total_modified += 1
                    
                    if 'dynastyPinyin' in content_item:
                        del content_item['dynastyPinyin']
                        file_modified = True
                        total_modified += 1
            
            # 保存修改
            if file_modified:
                with open(txt_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent='\t')
                files_modified.append(txt_file.name)
                print(f"已保存: {txt_file.name}\n")
        
        except Exception as e:
            print(f"处理文件 {txt_file.name} 时出错: {str(e)}\n")
    
    print("=" * 80)
    print("处理完成")
    print("=" * 80)
    print(f"总计修改 {total_modified} 处")
    print(f"修改了 {len(files_modified)} 个文件:")
    for filename in files_modified:
        print(f"  - {filename}")

if __name__ == "__main__":
    print("开始处理1年级文章格式...")
    print("=" * 80)
    process_grade1_files()

