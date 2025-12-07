#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面检查2年级内容，包括：
1. 内容逻辑检查：逻辑错误、前后矛盾、前后句毫无关联等
2. 拼音检查：拼音里有标点符号、汉字和拼音必须匹配、拼音数量对应等
"""
import json
import os
import re
from pathlib import Path
from collections import defaultdict

def extract_chinese_chars(text):
    """提取文本中的汉字"""
    return ''.join(re.findall(r'[\u4e00-\u9fff]', text))

def extract_pinyin_words(pinyin):
    """提取拼音中的拼音词（去除标点）"""
    # 拼音词通常由字母和声调组成，用空格分隔
    # 移除标点符号，只保留拼音词
    pinyin_clean = re.sub(r'[^\w\s\u0100-\u017F]', '', pinyin)  # 保留字母、数字、空格和带声调的字母
    words = [w.strip() for w in pinyin_clean.split() if w.strip()]
    return words

def count_pinyin_syllables(pinyin):
    """统计拼音音节数量（考虑声调）"""
    # 拼音音节通常以空格分隔，每个音节可能包含声调
    words = extract_pinyin_words(pinyin)
    return len(words)

def check_pinyin_issues(content_item, file_ref):
    """检查拼音相关问题"""
    issues = []
    
    # 检查contentObject中的拼音
    for obj in content_item.get('contentObject', []):
        if isinstance(obj, dict):
            # 检查直接包含text和pinyin的情况
            if 'text' in obj and 'pinyin' in obj:
                text = obj['text']
                pinyin = obj['pinyin']
                
                # 1. 检查拼音中是否包含标点符号（不应该有）
                pinyin_punctuation = re.findall(r'[，。！？、；：""''（）【】《》〈〉『』「」]', pinyin)
                if pinyin_punctuation:
                    issues.append({
                        "type": "拼音包含标点符号",
                        "file": file_ref,
                        "title": content_item.get('title', ''),
                        "text": text,
                        "pinyin": pinyin,
                        "problem": f"拼音中包含标点符号：{set(pinyin_punctuation)}"
                    })
                
                # 2. 检查汉字和拼音数量是否对应
                chinese_chars = extract_chinese_chars(text)
                pinyin_syllables = count_pinyin_syllables(pinyin)
                
                if chinese_chars and pinyin_syllables > 0:
                    # 允许一定的误差（因为可能有标点、数字等）
                    # 但拼音数量应该接近汉字数量
                    char_count = len(chinese_chars)
                    diff = abs(pinyin_syllables - char_count)
                    
                    # 如果差异超过20%且超过2个，可能有问题
                    if diff > max(2, char_count * 0.2) and char_count > 3:
                        issues.append({
                            "type": "拼音与汉字数量不匹配",
                            "file": file_ref,
                            "title": content_item.get('title', ''),
                            "text": text,
                            "pinyin": pinyin,
                            "problem": f"汉字数：{char_count}，拼音音节数：{pinyin_syllables}，差异：{diff}"
                        })
                
                # 3. 检查拼音格式是否正确（应该只包含字母、声调和空格）
                invalid_chars = re.findall(r'[^\w\s\u0100-\u017F\u00C0-\u00FF]', pinyin)
                # 排除常见的标点符号（这些已经在上面检查过了）
                invalid_chars = [c for c in invalid_chars if c not in '，。！？、；：""''（）【】《》〈〉『』「」']
                if invalid_chars:
                    issues.append({
                        "type": "拼音格式不正确",
                        "file": file_ref,
                        "title": content_item.get('title', ''),
                        "text": text,
                        "pinyin": pinyin,
                        "problem": f"拼音中包含无效字符：{set(invalid_chars)}"
                    })
            
            # 检查嵌套的content（日积月累类型）
            elif 'content' in obj:
                for sub_item in obj.get('content', []):
                    if 'text' in sub_item and 'pinyin' in sub_item:
                        text = sub_item['text']
                        pinyin = sub_item['pinyin']
                        
                        # 同样的检查
                        pinyin_punctuation = re.findall(r'[，。！？、；：""''（）【】《》〈〉『』「」]', pinyin)
                        if pinyin_punctuation:
                            issues.append({
                                "type": "拼音包含标点符号",
                                "file": file_ref,
                                "title": content_item.get('title', ''),
                                "text": text,
                                "pinyin": pinyin,
                                "problem": f"拼音中包含标点符号：{set(pinyin_punctuation)}"
                            })
                        
                        chinese_chars = extract_chinese_chars(text)
                        pinyin_syllables = count_pinyin_syllables(pinyin)
                        
                        if chinese_chars and pinyin_syllables > 0:
                            char_count = len(chinese_chars)
                            diff = abs(pinyin_syllables - char_count)
                            if diff > max(2, char_count * 0.2) and char_count > 3:
                                issues.append({
                                    "type": "拼音与汉字数量不匹配",
                                    "file": file_ref,
                                    "title": content_item.get('title', ''),
                                    "text": text,
                                    "pinyin": pinyin,
                                    "problem": f"汉字数：{char_count}，拼音音节数：{pinyin_syllables}，差异：{diff}"
                                })
    
    # 检查taskPinyin
    if 'taskPinyin' in content_item and content_item['taskPinyin']:
        task_pinyin = content_item['taskPinyin']
        task_text = content_item.get('task', '')
        
        # 检查taskPinyin中是否包含标点符号
        pinyin_punctuation = re.findall(r'[，。！？、；：""''（）【】《》〈〉『』「」]', task_pinyin)
        if pinyin_punctuation:
            issues.append({
                "type": "taskPinyin包含标点符号",
                "file": file_ref,
                "title": content_item.get('title', ''),
                "text": task_text,
                "pinyin": task_pinyin,
                "problem": f"taskPinyin中包含标点符号：{set(pinyin_punctuation)}"
            })
        
        # 检查taskPinyin和task的匹配
        chinese_chars = extract_chinese_chars(task_text)
        pinyin_syllables = count_pinyin_syllables(task_pinyin)
        if chinese_chars and pinyin_syllables > 0:
            char_count = len(chinese_chars)
            diff = abs(pinyin_syllables - char_count)
            if diff > max(2, char_count * 0.2) and char_count > 3:
                issues.append({
                    "type": "taskPinyin与task不匹配",
                    "file": file_ref,
                    "title": content_item.get('title', ''),
                    "text": task_text,
                    "pinyin": task_pinyin,
                    "problem": f"task汉字数：{char_count}，taskPinyin音节数：{pinyin_syllables}，差异：{diff}"
                })
    
    # 检查taskAnswerPinyin
    if 'taskAnswerPinyin' in content_item and content_item['taskAnswerPinyin']:
        answer_pinyin = content_item['taskAnswerPinyin']
        answer_text = content_item.get('taskAnswer', '')
        
        # 检查taskAnswerPinyin中是否包含标点符号
        pinyin_punctuation = re.findall(r'[，。！？、；：""''（）【】《》〈〉『』「」]', answer_pinyin)
        if pinyin_punctuation:
            issues.append({
                "type": "taskAnswerPinyin包含标点符号",
                "file": file_ref,
                "title": content_item.get('title', ''),
                "text": answer_text,
                "pinyin": answer_pinyin,
                "problem": f"taskAnswerPinyin中包含标点符号：{set(pinyin_punctuation)}"
            })
        
        # 检查taskAnswerPinyin和taskAnswer的匹配
        chinese_chars = extract_chinese_chars(answer_text)
        pinyin_syllables = count_pinyin_syllables(answer_pinyin)
        if chinese_chars and pinyin_syllables > 0:
            char_count = len(chinese_chars)
            diff = abs(pinyin_syllables - char_count)
            if diff > max(2, char_count * 0.2) and char_count > 3:
                issues.append({
                    "type": "taskAnswerPinyin与taskAnswer不匹配",
                    "file": file_ref,
                    "title": content_item.get('title', ''),
                    "text": answer_text,
                    "pinyin": answer_pinyin,
                    "problem": f"taskAnswer汉字数：{char_count}，taskAnswerPinyin音节数：{pinyin_syllables}，差异：{diff}"
                })
    
    # 检查其他包含拼音的字段
    pinyin_fields = ['titlePinyin', 'authorPinyin', 'dynastyPinyin', 'annotationPinyin', 'translationPinyin']
    for field in pinyin_fields:
        if field in content_item and content_item[field]:
            pinyin = content_item[field]
            pinyin_punctuation = re.findall(r'[，。！？、；：""''（）【】《》〈〉『』「」]', pinyin)
            if pinyin_punctuation:
                issues.append({
                    "type": f"{field}包含标点符号",
                    "file": file_ref,
                    "title": content_item.get('title', ''),
                    "pinyin": pinyin,
                    "problem": f"{field}中包含标点符号：{set(pinyin_punctuation)}"
                })
    
    return issues

def check_logic_issues(content_item, file_ref, all_content_text=""):
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
                    if 'text' in sub_item:
                        content_texts.append(sub_item['text'])
    
    full_text = ''.join(content_texts)
    
    if not full_text:
        return issues
    
    # 1. 检查前后句是否毫无关联（硬凑在一起）
    sentences = re.split(r'[。！？]', full_text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 2]
    
    if len(sentences) >= 2:
        # 检查相邻句子之间的关联性
        for i in range(len(sentences) - 1):
            sent1 = sentences[i]
            sent2 = sentences[i + 1]
            
            # 检查是否有明显的主题切换（可能是硬凑）
            # 简单检查：如果两句完全没有共同词汇，且都很短，可能是硬凑
            common_chars = set(sent1) & set(sent2)
            if len(common_chars) == 0 and len(sent1) < 10 and len(sent2) < 10:
                # 进一步检查：是否是完全不同的主题
                animal_keywords = ['猫', '狗', '鸟', '鱼', '兔', '熊', '虎', '狮', '象', '猴', '鸡', '鸭', '鹅', '蛙', '蝌蚪']
                color_keywords = ['红', '绿', '蓝', '黄', '白', '黑', '紫', '橙', '碧', '雪']
                number_keywords = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
                weather_keywords = ['雨', '雪', '风', '云', '太阳', '月亮', '星星']
                plant_keywords = ['花', '草', '树', '叶', '莲', '荷']
                
                sent1_has_animal = any(kw in sent1 for kw in animal_keywords)
                sent1_has_color = any(kw in sent1 for kw in color_keywords)
                sent1_has_number = any(kw in sent1 for kw in number_keywords)
                sent1_has_weather = any(kw in sent1 for kw in weather_keywords)
                sent1_has_plant = any(kw in sent1 for kw in plant_keywords)
                
                sent2_has_animal = any(kw in sent2 for kw in animal_keywords)
                sent2_has_color = any(kw in sent2 for kw in color_keywords)
                sent2_has_number = any(kw in sent2 for kw in number_keywords)
                sent2_has_weather = any(kw in sent2 for kw in weather_keywords)
                sent2_has_plant = any(kw in sent2 for kw in plant_keywords)
                
                # 如果两句主题完全不同，可能是硬凑
                if ((sent1_has_animal and (sent2_has_color or sent2_has_weather or sent2_has_plant)) or
                    (sent1_has_color and (sent2_has_animal or sent2_has_weather)) or
                    (sent1_has_weather and (sent2_has_animal or sent2_has_color))):
                    issues.append({
                        "type": "前后句毫无关联",
                        "file": file_ref,
                        "title": content_item.get('title', ''),
                        "problem": f"相邻句子主题完全不同，可能是硬凑：\n  前句：{sent1}\n  后句：{sent2}"
                    })
    
    # 2. 检查逻辑矛盾
    content_type = content_item.get('type', '')
    title = content_item.get('title', '')
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
        if len(time_found) > 1 and len(full_text) < 50:
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
                    "title": content_item.get('title', ''),
                    "problem": f"短文本中同时出现多个时间概念：{time_found}，可能存在时间矛盾"
                })
    
    # 3. 检查前后矛盾
    # 检查肯定和否定的矛盾（排除绕口令等特殊类型）
    if content_type not in ['tongue_twisters']:
        positive_words = ['是', '有', '能', '会', '好', '对', '正确']
        negative_words = ['不是', '没有', '不能', '不会', '不好', '不对', '错误']
        
        has_positive = any(word in full_text for word in positive_words)
        has_negative = any(word in full_text for word in negative_words)
        
        # 如果短文本中同时出现肯定和否定，可能是矛盾
        if has_positive and has_negative and len(full_text) < 30:
            # 检查是否是明显的对比结构（如"是...不是..."）
            if not (('是' in full_text and '不是' in full_text) or 
                   ('有' in full_text and '没有' in full_text) or
                   ('能' in full_text and '不能' in full_text)):
                issues.append({
                    "type": "前后矛盾",
                    "file": file_ref,
                    "title": content_item.get('title', ''),
                    "problem": f"短文本中同时出现肯定和否定，可能存在矛盾：{full_text[:50]}"
                })
    
    # 4. 检查内容是否过于简短或不完整
    if content_type in ['modern_prose', 'story_legend', 'textbook_review']:
        if len(full_text) < 20 and len(sentences) < 3:
            issues.append({
                "type": "内容过于简短",
                "file": file_ref,
                "title": content_item.get('title', ''),
                "problem": f"内容过于简短，可能不够完整：{full_text[:50]}"
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
                    "title": content_item.get('title', ''),
                    "problem": f"发现重复的句子：{sent1}"
                })
    
    return issues

def check_grade2_content():
    """全面检查2年级内容"""
    base_dir = Path(__file__).parent
    grade2_dir = base_dir / "有拼音" / "2年级"
    
    all_issues = {
        "pinyin_punctuation": [],  # 拼音包含标点符号
        "pinyin_mismatch": [],      # 拼音与汉字不匹配
        "pinyin_format": [],        # 拼音格式不正确
        "logic_unrelated": [],      # 前后句毫无关联
        "logic_time": [],           # 时间逻辑矛盾
        "logic_contradiction": [],  # 前后矛盾
        "content_short": [],        # 内容过于简短
        "content_repeat": [],       # 内容重复
        "errors": []                # 其他错误
    }
    
    txt_files = list(grade2_dir.glob("*.txt"))
    
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
                    
                    # 检查拼音问题
                    pinyin_issues = check_pinyin_issues(content_item, file_ref)
                    for issue in pinyin_issues:
                        if "包含标点符号" in issue["type"]:
                            all_issues["pinyin_punctuation"].append(issue)
                        elif "不匹配" in issue["type"]:
                            all_issues["pinyin_mismatch"].append(issue)
                        elif "格式不正确" in issue["type"]:
                            all_issues["pinyin_format"].append(issue)
                    
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
        
        except Exception as e:
            all_issues["errors"].append({
                "file": str(txt_file),
                "error": str(e)
            })
    
    return all_issues

def print_report(issues):
    """打印检查报告"""
    print("=" * 60)
    print("2年级内容全面检查报告")
    print("=" * 60)
    
    total_issues = sum(len(v) for v in issues.values())
    print(f"\n总计发现 {total_issues} 个问题\n")
    
    # 拼音包含标点符号
    if issues["pinyin_punctuation"]:
        print(f"\n【拼音包含标点符号】共 {len(issues['pinyin_punctuation'])} 处：")
        for item in issues["pinyin_punctuation"][:10]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            if 'text' in item:
                print(f"    文字：{item['text'][:50]}")
            print(f"    拼音：{item['pinyin'][:50]}")
            print(f"    问题：{item['problem']}")
        if len(issues["pinyin_punctuation"]) > 10:
            print(f"  ... 还有 {len(issues['pinyin_punctuation']) - 10} 处")
    
    # 拼音与汉字不匹配
    if issues["pinyin_mismatch"]:
        print(f"\n【拼音与汉字不匹配】共 {len(issues['pinyin_mismatch'])} 处：")
        for item in issues["pinyin_mismatch"][:10]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            if 'text' in item:
                print(f"    文字：{item['text'][:50]}")
            print(f"    拼音：{item['pinyin'][:50]}")
            print(f"    问题：{item['problem']}")
        if len(issues["pinyin_mismatch"]) > 10:
            print(f"  ... 还有 {len(issues['pinyin_mismatch']) - 10} 处")
    
    # 拼音格式不正确
    if issues["pinyin_format"]:
        print(f"\n【拼音格式不正确】共 {len(issues['pinyin_format'])} 处：")
        for item in issues["pinyin_format"][:5]:
            print(f"  - {item['file']}")
            print(f"    标题：{item['title']}")
            print(f"    拼音：{item['pinyin'][:50]}")
            print(f"    问题：{item['problem']}")
        if len(issues["pinyin_format"]) > 5:
            print(f"  ... 还有 {len(issues['pinyin_format']) - 5} 处")
    
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
        f.write("# 2年级内容全面检查报告\n\n")
        f.write("## 概述\n")
        f.write("本报告全面检查2年级所有教学内容文件，包括拼音检查和内容逻辑检查。\n\n")
        
        total_issues = sum(len(v) for v in issues.values())
        f.write(f"## 检查结果\n\n")
        f.write(f"总计发现 {total_issues} 个问题。\n\n")
        
        # 拼音问题
        f.write("## 一、拼音问题\n\n")
        
        if issues["pinyin_punctuation"]:
            f.write(f"### 1. 拼音包含标点符号 (共 {len(issues['pinyin_punctuation'])} 处)\n\n")
            for item in issues["pinyin_punctuation"]:
                f.write(f"- **文件位置**：{item['file']}\n")
                f.write(f"  - **标题**：{item['title']}\n")
                if 'text' in item:
                    f.write(f"  - **文字**：{item['text']}\n")
                f.write(f"  - **拼音**：{item['pinyin']}\n")
                f.write(f"  - **问题**：{item['problem']}\n\n")
        
        if issues["pinyin_mismatch"]:
            f.write(f"### 2. 拼音与汉字不匹配 (共 {len(issues['pinyin_mismatch'])} 处)\n\n")
            for item in issues["pinyin_mismatch"]:
                f.write(f"- **文件位置**：{item['file']}\n")
                f.write(f"  - **标题**：{item['title']}\n")
                if 'text' in item:
                    f.write(f"  - **文字**：{item['text']}\n")
                f.write(f"  - **拼音**：{item['pinyin']}\n")
                f.write(f"  - **问题**：{item['problem']}\n\n")
        
        if issues["pinyin_format"]:
            f.write(f"### 3. 拼音格式不正确 (共 {len(issues['pinyin_format'])} 处)\n\n")
            for item in issues["pinyin_format"]:
                f.write(f"- **文件位置**：{item['file']}\n")
                f.write(f"  - **标题**：{item['title']}\n")
                f.write(f"  - **拼音**：{item['pinyin']}\n")
                f.write(f"  - **问题**：{item['problem']}\n\n")
        
        # 逻辑问题
        f.write("## 二、内容逻辑问题\n\n")
        
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
        
        # 其他错误
        if issues["errors"]:
            f.write("## 三、文件错误\n\n")
            for item in issues["errors"]:
                f.write(f"- **文件**：{item['file']}\n")
                f.write(f"  - **错误**：{item['error']}\n\n")
        
        f.write("## 优化建议\n\n")
        f.write("1. **修正拼音中的标点符号**：拼音字段中不应包含任何标点符号，只应包含拼音字母、声调和空格。\n")
        f.write("2. **修正拼音与汉字不匹配的问题**：仔细核对拼音，确保每个汉字都有对应的拼音，且数量匹配。\n")
        f.write("3. **修正前后句毫无关联的问题**：检查内容是否连贯，确保相邻句子之间有逻辑联系。\n")
        f.write("4. **修正时间逻辑矛盾**：确保时间描述的一致性，避免在短文本中出现矛盾的时间概念。\n")
        f.write("5. **修正前后矛盾**：检查内容中是否存在肯定和否定的矛盾。\n")
        f.write("6. **补充过于简短的内容**：对于过于简短的内容，考虑补充更多细节。\n")
        f.write("7. **删除重复内容**：删除或修改重复的句子。\n")

if __name__ == "__main__":
    issues = check_grade2_content()
    print_report(issues)
    
    # 保存详细报告到文件
    base_dir = Path(__file__).parent
    report_file = base_dir / "2年级内容全面检查报告.md"
    save_report_to_file(issues, report_file)
    print(f"\n详细报告已保存到: {report_file}")

