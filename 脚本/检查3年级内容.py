#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查3年级内容的不合理之处：
1. 内容逻辑检查：逻辑错误、前后矛盾、前后文毫无关联等
2. 内容合理性检查：难度是否合适、内容是否完整等
"""
import json
import os
import re
from pathlib import Path
from collections import defaultdict

def check_logic_issues(content_item, file_ref):
    """检查内容逻辑问题"""
    issues = []
    
    # 收集所有文本内容
    content_texts = []
    for obj in content_item.get('contentObject', []):
        if isinstance(obj, dict):
            if 'text' in obj:
                content_texts.append(obj['text'])
            elif 'content' in obj:
                for sub_item in obj.get('content', []):
                    if isinstance(sub_item, dict) and 'text' in sub_item:
                        content_texts.append(sub_item['text'])
    
    full_text = ''.join(content_texts)
    
    if not full_text:
        return issues
    
    content_type = content_item.get('type', '')
    title = content_item.get('title', '')
    
    # 1. 检查前后句是否毫无关联（硬凑在一起）
    sentences = re.split(r'[。！？]', full_text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 2]
    
    if len(sentences) >= 2:
        # 检查相邻句子之间的关联性
        for i in range(len(sentences) - 1):
            sent1 = sentences[i]
            sent2 = sentences[i + 1]
            
            # 检查是否有明显的主题切换（可能是硬凑）
            common_chars = set(sent1) & set(sent2)
            if len(common_chars) == 0 and len(sent1) < 15 and len(sent2) < 15:
                # 进一步检查：是否是完全不同的主题
                animal_keywords = ['猫', '狗', '鸟', '鱼', '兔', '熊', '虎', '狮', '象', '猴', '鸡', '鸭', '鹅', '蛙', '蝌蚪', '蝉', '牧童']
                color_keywords = ['红', '绿', '蓝', '黄', '白', '黑', '紫', '橙', '碧', '雪', '翠', '金黄']
                weather_keywords = ['雨', '雪', '风', '云', '太阳', '月亮', '星星', '晴天', '阴天']
                plant_keywords = ['花', '草', '树', '叶', '莲', '荷', '梧桐', '绒球花']
                school_keywords = ['学校', '校园', '教室', '操场', '老师', '同学', '学生']
                
                sent1_has_animal = any(kw in sent1 for kw in animal_keywords)
                sent1_has_color = any(kw in sent1 for kw in color_keywords)
                sent1_has_weather = any(kw in sent1 for kw in weather_keywords)
                sent1_has_plant = any(kw in sent1 for kw in plant_keywords)
                sent1_has_school = any(kw in sent1 for kw in school_keywords)
                
                sent2_has_animal = any(kw in sent2 for kw in animal_keywords)
                sent2_has_color = any(kw in sent2 for kw in color_keywords)
                sent2_has_weather = any(kw in sent2 for kw in weather_keywords)
                sent2_has_plant = any(kw in sent2 for kw in plant_keywords)
                sent2_has_school = any(kw in sent2 for kw in school_keywords)
                
                # 如果两句主题完全不同，可能是硬凑
                if ((sent1_has_animal and (sent2_has_color or sent2_has_weather or sent2_has_plant or sent2_has_school)) or
                    (sent1_has_color and (sent2_has_animal or sent2_has_weather)) or
                    (sent1_has_weather and (sent2_has_animal or sent2_has_color)) or
                    (sent1_has_school and (sent2_has_animal and not sent2_has_school))):
                    issues.append({
                        "type": "前后句毫无关联",
                        "file": file_ref,
                        "title": title,
                        "problem": f"相邻句子主题完全不同，可能是硬凑：\n  前句：{sent1}\n  后句：{sent2}"
                    })
    
    # 2. 检查逻辑矛盾
    # 检查时间矛盾（排除日积月累类型中的句式练习）
    is_sentence_pattern = ('什么时候' in title or '句式' in title or '学说一句话' in title or 
                          '说一句话' in title or '句式练习' in title)
    
    if not (content_type == 'daily_accumulation' and is_sentence_pattern):
        time_keywords = {
            '早上': ['早上', '早晨', '清晨', '上午'],
            '中午': ['中午', '正午', '午时'],
            '下午': ['下午', '午后'],
            '晚上': ['晚上', '夜晚', '夜里', '深夜', '傍晚', '黄昏']
        }
        
        time_found = set()
        for time_type, keywords in time_keywords.items():
            for keyword in keywords:
                if keyword in full_text:
                    time_found.add(time_type)
                    break
        
        # 如果短文本中同时出现多个时间，可能是矛盾
        if len(time_found) > 1 and len(full_text) < 80:
            # 检查是否是并列的句式练习（每个句子都以时间开头）
            sentences = re.split(r'[。！？]', full_text)
            time_start_count = 0
            for sent in sentences:
                sent = sent.strip()
                if sent:
                    # 检查句子是否以时间词开头
                    for time_type, keywords in time_keywords.items():
                        for keyword in keywords:
                            if sent.startswith(keyword):
                                time_start_count += 1
                                break
            
            # 如果大部分句子都以时间开头，这是正常的句式练习，不是矛盾
            if time_start_count < len([s for s in sentences if s.strip()]) * 0.6:
                issues.append({
                    "type": "时间逻辑矛盾",
                    "file": file_ref,
                    "title": title,
                    "problem": f"短文本中同时出现多个时间概念：{time_found}，可能存在时间矛盾"
                })
    
    # 3. 检查前后矛盾
    # 检查肯定和否定的矛盾（排除绕口令等特殊类型）
    if content_type not in ['tongue_twisters']:
        positive_words = ['是', '有', '能', '会', '好', '对', '正确', '应该', '必须']
        negative_words = ['不是', '没有', '不能', '不会', '不好', '不对', '错误', '不应该', '不必']
        
        has_positive = any(word in full_text for word in positive_words)
        has_negative = any(word in full_text for word in negative_words)
        
        # 如果短文本中同时出现肯定和否定，可能是矛盾
        if has_positive and has_negative and len(full_text) < 50:
            # 检查是否是明显的对比结构（如"是...不是..."）
            if not (('是' in full_text and '不是' in full_text) or 
                   ('有' in full_text and '没有' in full_text) or
                   ('能' in full_text and '不能' in full_text) or
                   ('应该' in full_text and '不应该' in full_text)):
                issues.append({
                    "type": "前后矛盾",
                    "file": file_ref,
                    "title": title,
                    "problem": f"短文本中同时出现肯定和否定，可能存在矛盾：{full_text[:80]}"
                })
    
    # 4. 检查内容是否过于简短或不完整
    if content_type in ['modern_prose', 'story_legend', 'textbook_review']:
        if len(full_text) < 30 and len(sentences) < 3:
            issues.append({
                "type": "内容过于简短",
                "file": file_ref,
                "title": title,
                "problem": f"内容过于简短，可能不够完整：{full_text[:80]}"
            })
    
    # 5. 检查重复内容
    if len(sentences) >= 2:
        for i in range(len(sentences) - 1):
            sent1 = sentences[i]
            sent2 = sentences[i + 1]
            # 如果两句几乎完全相同，可能是重复
            if sent1 == sent2 and len(sent1) > 5:
                issues.append({
                    "type": "内容重复",
                    "file": file_ref,
                    "title": title,
                    "problem": f"发现重复的句子：{sent1}"
                })
    
    # 6. 检查内容难度是否合适（对3年级来说）
    # 检查是否有过于复杂的词汇或表达
    if content_type in ['modern_prose', 'textbook_review']:
        complex_words_3grade = [
            "经验丰富", "耐心地", "巨大的", "广阔的", "缓缓", "善良的",
            "哲学", "理论", "抽象", "概念", "原理", "机制", "系统",
            "复杂", "深奥", "高深", "专业术语"
        ]
        for word in complex_words_3grade:
            if word in full_text:
                issues.append({
                    "type": "难度不匹配",
                    "file": file_ref,
                    "title": title,
                    "problem": f"内容可能过于复杂，不适合3年级学生：包含词汇'{word}'"
                })
                break
    
    # 7. 检查annotation格式（应该只包含字词解释）
    if 'annotation' in content_item and content_item['annotation']:
        annotation = content_item['annotation']
        # 检查是否包含说明性句子（不是字词解释格式）
        if '这是' in annotation or '表达' in annotation or '说明' in annotation:
            if not re.search(r'[：:].*[。！]', annotation):  # 如果不是字词解释格式
                issues.append({
                    "type": "注解格式问题",
                    "file": file_ref,
                    "title": title,
                    "problem": f"注解应只包含字词解释，不应包含说明性句子：{annotation[:100]}"
                })
    
    # 8. 检查task和taskAnswer是否匹配
    task = content_item.get('task', '')
    task_answer = content_item.get('taskAnswer', '')
    if task and task_answer:
        # 检查task是否是问句，taskAnswer是否回答了问题
        if '？' in task or '?' in task or '什么' in task or '怎么' in task or '为什么' in task or '哪里' in task:
            # task是问句，taskAnswer应该给出答案
            if len(task_answer) < 5:
                issues.append({
                    "type": "任务答案不匹配",
                    "file": file_ref,
                    "title": title,
                    "problem": f"任务问题是问句，但答案过于简短：\n  问题：{task}\n  答案：{task_answer}"
                })
    
    return issues

def check_grade3_content():
    """全面检查3年级内容"""
    base_dir = Path(__file__).parent
    grade3_dir = base_dir / "无拼音" / "3年级"
    
    if not grade3_dir.exists():
        print(f"错误：未找到3年级内容路径: {grade3_dir}")
        return {}
    
    all_issues = {
        "logic_unrelated": [],      # 前后句毫无关联
        "logic_time": [],           # 时间逻辑矛盾
        "logic_contradiction": [],  # 前后矛盾
        "content_short": [],        # 内容过于简短
        "content_repeat": [],       # 内容重复
        "difficulty_issues": [],    # 难度不匹配
        "annotation_issues": [],    # 注解格式问题
        "task_answer_issues": [],   # 任务答案不匹配
        "errors": []                # 其他错误
    }
    
    txt_files = sorted(grade3_dir.glob("*.txt"))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for week_data in data:
                week_num = week_data.get('week', 0)
                day_num = week_data.get('day', 0)
                theme = week_data.get('theme', '')
                
                for content_item in week_data.get('content', []):
                    file_ref = f"{txt_file.name} - 第{week_num}周第{day_num}天 - {theme}"
                    
                    # 检查逻辑问题
                    logic_issues = check_logic_issues(content_item, file_ref)
                    for issue in logic_issues:
                        if issue["type"] == "前后句毫无关联":
                            all_issues["logic_unrelated"].append(issue)
                        elif issue["type"] == "时间逻辑矛盾":
                            all_issues["logic_time"].append(issue)
                        elif issue["type"] == "前后矛盾":
                            all_issues["logic_contradiction"].append(issue)
                        elif issue["type"] == "内容过于简短":
                            all_issues["content_short"].append(issue)
                        elif issue["type"] == "内容重复":
                            all_issues["content_repeat"].append(issue)
                        elif issue["type"] == "难度不匹配":
                            all_issues["difficulty_issues"].append(issue)
                        elif issue["type"] == "注解格式问题":
                            all_issues["annotation_issues"].append(issue)
                        elif issue["type"] == "任务答案不匹配":
                            all_issues["task_answer_issues"].append(issue)
        
        except Exception as e:
            all_issues["errors"].append({
                "file": str(txt_file),
                "error": str(e)
            })
    
    return all_issues

def print_report(issues):
    """打印检查报告"""
    print("=" * 60)
    print("3年级内容检查报告")
    print("=" * 60)
    
    total_issues = sum(len(v) for v in issues.values())
    print(f"\n总计发现 {total_issues} 个问题\n")
    
    # 前后句毫无关联
    if issues["logic_unrelated"]:
        print(f"\n【前后句毫无关联】共 {len(issues['logic_unrelated'])} 处：")
        for item in issues["logic_unrelated"][:5]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    问题：{item['problem']}")
        if len(issues["logic_unrelated"]) > 5:
            print(f"  ... 还有 {len(issues['logic_unrelated']) - 5} 处")
    
    # 时间逻辑矛盾
    if issues["logic_time"]:
        print(f"\n【时间逻辑矛盾】共 {len(issues['logic_time'])} 处：")
        for item in issues["logic_time"][:5]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    问题：{item['problem']}")
        if len(issues["logic_time"]) > 5:
            print(f"  ... 还有 {len(issues['logic_time']) - 5} 处")
    
    # 前后矛盾
    if issues["logic_contradiction"]:
        print(f"\n【前后矛盾】共 {len(issues['logic_contradiction'])} 处：")
        for item in issues["logic_contradiction"][:5]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    问题：{item['problem']}")
        if len(issues["logic_contradiction"]) > 5:
            print(f"  ... 还有 {len(issues['logic_contradiction']) - 5} 处")
    
    # 内容过于简短
    if issues["content_short"]:
        print(f"\n【内容过于简短】共 {len(issues['content_short'])} 处：")
        for item in issues["content_short"][:5]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    问题：{item['problem']}")
        if len(issues["content_short"]) > 5:
            print(f"  ... 还有 {len(issues['content_short']) - 5} 处")
    
    # 内容重复
    if issues["content_repeat"]:
        print(f"\n【内容重复】共 {len(issues['content_repeat'])} 处：")
        for item in issues["content_repeat"][:5]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    问题：{item['problem']}")
        if len(issues["content_repeat"]) > 5:
            print(f"  ... 还有 {len(issues['content_repeat']) - 5} 处")
    
    # 难度不匹配
    if issues["difficulty_issues"]:
        print(f"\n【难度不匹配】共 {len(issues['difficulty_issues'])} 处：")
        for item in issues["difficulty_issues"][:5]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    问题：{item['problem']}")
        if len(issues["difficulty_issues"]) > 5:
            print(f"  ... 还有 {len(issues['difficulty_issues']) - 5} 处")
    
    # 注解格式问题
    if issues["annotation_issues"]:
        print(f"\n【注解格式问题】共 {len(issues['annotation_issues'])} 处：")
        for item in issues["annotation_issues"][:5]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    问题：{item['problem']}")
        if len(issues["annotation_issues"]) > 5:
            print(f"  ... 还有 {len(issues['annotation_issues']) - 5} 处")
    
    # 任务答案不匹配
    if issues["task_answer_issues"]:
        print(f"\n【任务答案不匹配】共 {len(issues['task_answer_issues'])} 处：")
        for item in issues["task_answer_issues"][:5]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    问题：{item['problem']}")
        if len(issues["task_answer_issues"]) > 5:
            print(f"  ... 还有 {len(issues['task_answer_issues']) - 5} 处")
    
    # 其他错误
    if issues["errors"]:
        print(f"\n【文件错误】共 {len(issues['errors'])} 处：")
        for item in issues["errors"]:
            print(f"  - {item['file']}")
            print(f"    错误：{item['error']}")
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

def save_report_to_file(issues, output_file):
    """保存详细报告到文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 3年级内容检查报告\n\n")
        f.write("## 概述\n")
        f.write("本报告全面检查3年级所有教学内容文件，包括内容逻辑检查和合理性检查。\n\n")
        
        total_issues = sum(len(v) for v in issues.values())
        f.write(f"## 检查结果\n\n")
        f.write(f"总计发现 {total_issues} 个问题。\n\n")
        
        # 逻辑问题
        f.write("## 一、内容逻辑问题\n\n")
        
        if issues["logic_unrelated"]:
            f.write(f"### 1. 前后句毫无关联 (共 {len(issues['logic_unrelated'])} 处)\n\n")
            for item in issues["logic_unrelated"]:
                f.write(f"- **文件位置**：{item['file']}\n")
                f.write(f"  - **标题**：{item['title']}\n")
                f.write(f"  - **问题**：{item['problem']}\n\n")
        
        if issues["logic_time"]:
            f.write(f"### 2. 时间逻辑矛盾 (共 {len(issues['logic_time'])} 处)\n\n")
            for item in issues["logic_time"]:
                f.write(f"- **文件位置**：{item['file']}\n")
                f.write(f"  - **标题**：{item['title']}\n")
                f.write(f"  - **问题**：{item['problem']}\n\n")
        
        if issues["logic_contradiction"]:
            f.write(f"### 3. 前后矛盾 (共 {len(issues['logic_contradiction'])} 处)\n\n")
            for item in issues["logic_contradiction"]:
                f.write(f"- **文件位置**：{item['file']}\n")
                f.write(f"  - **标题**：{item['title']}\n")
                f.write(f"  - **问题**：{item['problem']}\n\n")
        
        if issues["content_short"]:
            f.write(f"### 4. 内容过于简短 (共 {len(issues['content_short'])} 处)\n\n")
            for item in issues["content_short"]:
                f.write(f"- **文件位置**：{item['file']}\n")
                f.write(f"  - **标题**：{item['title']}\n")
                f.write(f"  - **问题**：{item['problem']}\n\n")
        
        if issues["content_repeat"]:
            f.write(f"### 5. 内容重复 (共 {len(issues['content_repeat'])} 处)\n\n")
            for item in issues["content_repeat"]:
                f.write(f"- **文件位置**：{item['file']}\n")
                f.write(f"  - **标题**：{item['title']}\n")
                f.write(f"  - **问题**：{item['problem']}\n\n")
        
        # 其他问题
        f.write("## 二、其他问题\n\n")
        
        if issues["difficulty_issues"]:
            f.write(f"### 1. 难度不匹配 (共 {len(issues['difficulty_issues'])} 处)\n\n")
            for item in issues["difficulty_issues"]:
                f.write(f"- **文件位置**：{item['file']}\n")
                f.write(f"  - **标题**：{item['title']}\n")
                f.write(f"  - **问题**：{item['problem']}\n\n")
        
        if issues["annotation_issues"]:
            f.write(f"### 2. 注解格式问题 (共 {len(issues['annotation_issues'])} 处)\n\n")
            for item in issues["annotation_issues"]:
                f.write(f"- **文件位置**：{item['file']}\n")
                f.write(f"  - **标题**：{item['title']}\n")
                f.write(f"  - **问题**：{item['problem']}\n\n")
        
        if issues["task_answer_issues"]:
            f.write(f"### 3. 任务答案不匹配 (共 {len(issues['task_answer_issues'])} 处)\n\n")
            for item in issues["task_answer_issues"]:
                f.write(f"- **文件位置**：{item['file']}\n")
                f.write(f"  - **标题**：{item['title']}\n")
                f.write(f"  - **问题**：{item['problem']}\n\n")
        
        # 其他错误
        if issues["errors"]:
            f.write("## 三、文件错误\n\n")
            for item in issues["errors"]:
                f.write(f"- **文件**：{item['file']}\n")
                f.write(f"  - **错误**：{item['error']}\n\n")
        
        f.write("## 优化建议\n\n")
        f.write("1. **修正前后句毫无关联的问题**：检查内容是否连贯，确保相邻句子之间有逻辑联系。\n")
        f.write("2. **修正时间逻辑矛盾**：确保时间描述的一致性，避免在短文本中出现矛盾的时间概念。\n")
        f.write("3. **修正前后矛盾**：检查内容中是否存在肯定和否定的矛盾。\n")
        f.write("4. **补充过于简短的内容**：对于过于简短的内容，考虑补充更多细节。\n")
        f.write("5. **删除重复内容**：删除或修改重复的句子。\n")
        f.write("6. **调整难度不匹配的内容**：对于过于复杂的内容，考虑简化表达，或替换为更符合3年级学生认知水平的简单句式和词语。\n")
        f.write("7. **修正注解格式**：确保注解只包含字词解释，不包含说明性句子。\n")
        f.write("8. **完善任务答案**：确保任务答案能够充分回答任务问题。\n")

if __name__ == "__main__":
    issues = check_grade3_content()
    print_report(issues)
    
    # 保存详细报告到文件
    base_dir = Path(__file__).parent
    report_file = base_dir / "3年级内容检查报告.md"
    save_report_to_file(issues, report_file)
    print(f"\n详细报告已保存到: {report_file}")

