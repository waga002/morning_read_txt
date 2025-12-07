#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from pathlib import Path
from collections import defaultdict

def check_grade1_content():
    """检查1年级内容的问题"""
    base_dir = Path(__file__).parent
    grade1_dir = base_dir / "有拼音" / "1年级"
    
    issues = {
        "missing_task": [],
        "missing_taskPinyin": [],
        "missing_taskAnswer": [],
        "missing_fields": [],
        "content_issues": [],
        "pinyin_issues": [],
        "difficulty_issues": []
    }
    
    txt_files = list(grade1_dir.glob("*.txt"))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for week_data in data:
                week_num = week_data.get('week', 0)
                day_num = week_data.get('day', 0)
                theme = week_data.get('theme', '')
                
                for content_item in week_data.get('content', []):
                    title = content_item.get('title', '')
                    content_type = content_item.get('type', '')
                    file_ref = f"{txt_file.name} - 第{week_num}周第{day_num}天 - {theme}"
                    
                    # 检查task字段
                    if 'task' not in content_item or not content_item['task']:
                        issues["missing_task"].append({
                            "file": file_ref,
                            "title": title,
                            "type": content_type
                        })
                    
                    # 检查taskPinyin字段
                    if 'taskPinyin' not in content_item or not content_item['taskPinyin']:
                        if 'task' in content_item and content_item['task']:
                            issues["missing_taskPinyin"].append({
                                "file": file_ref,
                                "title": title,
                                "task": content_item.get('task', '')
                            })
                    
                    # 检查taskAnswer字段（某些类型可能需要答案）
                    if content_type in ['textbook_review', 'story_legend', 'ancient_poem']:
                        if 'taskAnswer' not in content_item:
                            issues["missing_taskAnswer"].append({
                                "file": file_ref,
                                "title": title,
                                "type": content_type
                            })
                    
                    # 检查contentObject
                    if 'contentObject' not in content_item:
                        issues["missing_fields"].append({
                            "file": file_ref,
                            "title": title,
                            "missing": "contentObject"
                        })
                    else:
                        # 检查contentObject中的拼音和文字是否匹配
                        for obj in content_item['contentObject']:
                            if 'pinyin' in obj and 'text' in obj:
                                pinyin = obj['pinyin']
                                text = obj['text']
                                # 简单检查：拼音和文字的数量应该大致匹配
                                pinyin_words = len([x for x in pinyin.split() if x.strip()])
                                text_chars = len([x for x in text if '\u4e00' <= x <= '\u9fff'])
                                if pinyin_words > 0 and text_chars > 0:
                                    # 拼音字数应该接近汉字数（考虑多音字和标点）
                                    if abs(pinyin_words - text_chars) > text_chars * 0.5 and text_chars > 3:
                                        issues["pinyin_issues"].append({
                                            "file": file_ref,
                                            "title": title,
                                            "pinyin": pinyin,
                                            "text": text,
                                            "pinyin_count": pinyin_words,
                                            "text_count": text_chars
                                        })
                    
                    # 检查内容难度
                    if content_type == 'ancient_poem':
                        # 检查古诗是否有合适的注释和翻译
                        if 'annotation' not in content_item or not content_item.get('annotation'):
                            issues["difficulty_issues"].append({
                                "file": file_ref,
                                "title": title,
                                "issue": "古诗缺少注释"
                            })
                        if 'translation' not in content_item or not content_item.get('translation'):
                            issues["difficulty_issues"].append({
                                "file": file_ref,
                                "title": title,
                                "issue": "古诗缺少翻译"
                            })
                    
                    # 检查日积月累类型的内容结构
                    if content_type == 'daily_accumulation':
                        if 'contentObject' in content_item:
                            for obj in content_item['contentObject']:
                                if 'content' in obj:
                                    for item in obj['content']:
                                        if 'pinyin' not in item or 'text' not in item:
                                            issues["missing_fields"].append({
                                                "file": file_ref,
                                                "title": title,
                                                "missing": "日积月累内容项缺少pinyin或text"
                                            })
        
        except Exception as e:
            issues["content_issues"].append({
                "file": str(txt_file),
                "error": str(e)
            })
    
    return issues

def print_report(issues):
    """打印检查报告"""
    print("=" * 60)
    print("1年级内容检查报告")
    print("=" * 60)
    
    total_issues = sum(len(v) for v in issues.values())
    print(f"\n总计发现 {total_issues} 个问题\n")
    
    # 缺少task字段
    if issues["missing_task"]:
        print(f"\n【缺少task字段】共 {len(issues['missing_task'])} 处：")
        for item in issues["missing_task"][:10]:  # 只显示前10个
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']} (类型：{item['type']})")
        if len(issues["missing_task"]) > 10:
            print(f"  ... 还有 {len(issues['missing_task']) - 10} 处")
    
    # 缺少taskPinyin字段
    if issues["missing_taskPinyin"]:
        print(f"\n【缺少taskPinyin字段】共 {len(issues['missing_taskPinyin'])} 处：")
        for item in issues["missing_taskPinyin"][:10]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    task：{item['task'][:50]}...")
        if len(issues["missing_taskPinyin"]) > 10:
            print(f"  ... 还有 {len(issues['missing_taskPinyin']) - 10} 处")
    
    # 缺少taskAnswer字段
    if issues["missing_taskAnswer"]:
        print(f"\n【缺少taskAnswer字段】共 {len(issues['missing_taskAnswer'])} 处：")
        for item in issues["missing_taskAnswer"][:10]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']} (类型：{item['type']})")
        if len(issues["missing_taskAnswer"]) > 10:
            print(f"  ... 还有 {len(issues['missing_taskAnswer']) - 10} 处")
    
    # 缺少其他字段
    if issues["missing_fields"]:
        print(f"\n【缺少其他字段】共 {len(issues['missing_fields'])} 处：")
        for item in issues["missing_fields"][:10]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    缺少：{item['missing']}")
        if len(issues["missing_fields"]) > 10:
            print(f"  ... 还有 {len(issues['missing_fields']) - 10} 处")
    
    # 拼音问题
    if issues["pinyin_issues"]:
        print(f"\n【拼音可能不匹配】共 {len(issues['pinyin_issues'])} 处：")
        for item in issues["pinyin_issues"][:5]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    文字：{item['text']}")
            print(f"    拼音：{item['pinyin']}")
            print(f"    拼音字数：{item['pinyin_count']}，汉字数：{item['text_count']}")
        if len(issues["pinyin_issues"]) > 5:
            print(f"  ... 还有 {len(issues['pinyin_issues']) - 5} 处")
    
    # 难度问题
    if issues["difficulty_issues"]:
        print(f"\n【难度相关问题】共 {len(issues['difficulty_issues'])} 处：")
        for item in issues["difficulty_issues"]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    问题：{item['issue']}")
    
    # 内容错误
    if issues["content_issues"]:
        print(f"\n【内容错误】共 {len(issues['content_issues'])} 处：")
        for item in issues["content_issues"]:
            print(f"  - {item['file']}")
            print(f"    错误：{item['error']}")
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == "__main__":
    issues = check_grade1_content()
    print_report(issues)

