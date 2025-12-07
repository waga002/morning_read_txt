#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查3-6年级古诗词（ancient_poem格式）是否需要拆分
如果单句超过5个字，且包含逗号分隔的两句，需要拆分
"""
import json
import re
from pathlib import Path

def count_chinese_chars(text):
    """统计文本中的汉字数量（排除标点、数字、字母）"""
    # 移除括号内的注音和标点
    text_clean = re.sub(r'（[^）]*）', '', text)  # 移除括号及内容
    text_clean = re.sub(r'\([^)]*\)', '', text_clean)  # 移除英文括号及内容
    # 统计汉字
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text_clean)
    return len(chinese_chars)

def check_ancient_poem_split(data, file_path):
    """检查古诗词是否需要拆分"""
    issues = []
    
    for week_data in data:
        week_num = week_data.get('week', 0)
        day_num = week_data.get('day', 0)
        theme = week_data.get('theme', '')
        
        for content_item in week_data.get('content', []):
            if content_item.get('type') == 'ancient_poem':
                title = content_item.get('title', '')
                file_ref = f"{file_path.name} - 第{week_num}周第{day_num}天 - {theme}"
                
                for obj in content_item.get('contentObject', []):
                    if isinstance(obj, dict) and 'text' in obj:
                        text = obj['text']
                        
                        # 检查是否包含逗号
                        if '，' in text or ',' in text:
                            # 检查逗号前后是否都有汉字
                            # 找到第一个逗号位置
                            comma_pos = text.find('，') if '，' in text else text.find(',')
                            if comma_pos > 0:
                                before_comma = text[:comma_pos].strip()
                                after_comma = text[comma_pos+1:].strip()
                                
                                # 统计逗号前后的汉字数量
                                before_chars = count_chinese_chars(before_comma)
                                after_chars = count_chinese_chars(after_comma)
                                
                                # 如果前后都有超过5个汉字，需要拆分
                                if before_chars > 5 and after_chars > 5:
                                    issues.append({
                                        "file": file_ref,
                                        "title": title,
                                        "text": text,
                                        "before_comma": before_comma,
                                        "after_comma": after_comma,
                                        "before_chars": before_chars,
                                        "after_chars": after_chars
                                    })
                
    return issues

def check_all_grades():
    """检查3-6年级的所有文件"""
    base_dir = Path(__file__).parent
    all_issues = []
    
    for grade in [3, 4, 5, 6]:
        grade_dir = base_dir / "无拼音" / f"{grade}年级"
        if not grade_dir.exists():
            continue
        
        txt_files = sorted(grade_dir.glob("*.txt"))
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                issues = check_ancient_poem_split(data, txt_file)
                all_issues.extend(issues)
            
            except Exception as e:
                print(f"处理文件 {txt_file.name} 时出错: {str(e)}")
    
    return all_issues

def print_report(issues):
    """打印检查报告"""
    print("=" * 80)
    print("3-6年级古诗词拆分检查报告")
    print("=" * 80)
    
    if not issues:
        print("\n✅ 未发现需要拆分的古诗词。")
        print("所有古诗词的单句都已正确拆分。")
        return
    
    print(f"\n发现 {len(issues)} 处需要拆分的古诗词：\n")
    
    # 按文件分组
    issues_by_file = {}
    for issue in issues:
        file_key = issue['file']
        if file_key not in issues_by_file:
            issues_by_file[file_key] = []
        issues_by_file[file_key].append(issue)
    
    for file_key, file_issues in issues_by_file.items():
        print(f"\n【{file_key}】")
        for issue in file_issues:
            print(f"\n  标题: {issue['title']}")
            print(f"  原文: {issue['text']}")
            print(f"  前句: {issue['before_comma']} ({issue['before_chars']}字)")
            print(f"  后句: {issue['after_comma']} ({issue['after_chars']}字)")
            print(f"  建议: 拆分成两行")
    
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)

if __name__ == "__main__":
    print("开始检查3-6年级古诗词拆分情况...")
    print()
    issues = check_all_grades()
    print_report(issues)
    
    # 保存详细报告
    if issues:
        base_dir = Path(__file__).parent
        report_file = base_dir / "古诗词拆分检查报告.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 3-6年级古诗词拆分检查报告\n\n")
            f.write("## 概述\n")
            f.write("检查3-6年级所有古诗词（ancient_poem格式），找出需要拆分的单句。\n\n")
            f.write(f"## 检查结果\n\n")
            f.write(f"发现 {len(issues)} 处需要拆分的古诗词。\n\n")
            
            # 按文件分组
            issues_by_file = {}
            for issue in issues:
                file_key = issue['file']
                if file_key not in issues_by_file:
                    issues_by_file[file_key] = []
                issues_by_file[file_key].append(issue)
            
            for file_key, file_issues in issues_by_file.items():
                f.write(f"### {file_key}\n\n")
                for issue in file_issues:
                    f.write(f"- **标题**: {issue['title']}\n")
                    f.write(f"  - **原文**: {issue['text']}\n")
                    f.write(f"  - **前句**: {issue['before_comma']} ({issue['before_chars']}字)\n")
                    f.write(f"  - **后句**: {issue['after_comma']} ({issue['after_chars']}字)\n")
                    f.write(f"  - **建议**: 拆分成两行\n\n")
        
        print(f"\n详细报告已保存到: {report_file}")

