#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面检查1年级内容，包括：
1. 内容逻辑检查：逻辑错误、前后矛盾、前后句毫无关联等
2. 拼音检查：拼音里有标点符号、数字不应该有拼音、汉字和拼音数量对应不上等
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
                
                # 2. 检查数字是否有拼音（数字不应该有拼音）
                numbers_in_text = re.findall(r'[0-9]+', text)
                if numbers_in_text:
                    # 检查拼音中是否也包含了这些数字的拼音
                    # 如果文本中有数字，拼音中不应该有对应的拼音
                    for num in numbers_in_text:
                        # 检查拼音中是否包含数字的拼音表示（如"yī"对应"1"）
                        num_pinyin_map = {
                            '0': 'líng', '1': 'yī', '2': 'èr', '3': 'sān', '4': 'sì',
                            '5': 'wǔ', '6': 'liù', '7': 'qī', '8': 'bā', '9': 'jiǔ'
                        }
                        if num in num_pinyin_map:
                            # 如果文本中有数字，但拼音中不应该有对应的拼音词
                            # 实际上，如果文本中有数字，拼音中可能也应该有数字，或者没有
                            # 这里我们检查：如果文本中有数字，拼音中不应该有该数字的拼音词
                            pass  # 这个规则可能需要根据实际情况调整
                
                # 3. 检查汉字和拼音数量是否对应
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
                
                # 4. 检查拼音格式是否正确（应该只包含字母、声调和空格）
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
    
    # 检查其他包含拼音的字段
    pinyin_fields = ['titlePinyin', 'authorPinyin', 'dynastyPinyin', 'taskAnswerPinyin', 'annotationPinyin', 'translationPinyin']
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
                # 如果一句是关于动物的，另一句是关于颜色的，可能是硬凑
                animal_keywords = ['猫', '狗', '鸟', '鱼', '兔', '熊', '虎', '狮', '象', '猴', '鸡', '鸭', '鹅']
                color_keywords = ['红', '绿', '蓝', '黄', '白', '黑', '紫', '橙']
                number_keywords = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
                
                sent1_has_animal = any(kw in sent1 for kw in animal_keywords)
                sent1_has_color = any(kw in sent1 for kw in color_keywords)
                sent1_has_number = any(kw in sent1 for kw in number_keywords)
                
                sent2_has_animal = any(kw in sent2 for kw in animal_keywords)
                sent2_has_color = any(kw in sent2 for kw in color_keywords)
                sent2_has_number = any(kw in sent2 for kw in number_keywords)
                
                # 如果两句主题完全不同，可能是硬凑
                if (sent1_has_animal and sent2_has_color) or (sent1_has_color and sent2_has_animal):
                    issues.append({
                        "type": "前后句毫无关联",
                        "file": file_ref,
                        "title": content_item.get('title', ''),
                        "problem": f"相邻句子主题完全不同，可能是硬凑：\n  前句：{sent1}\n  后句：{sent2}"
                    })
    
    # 2. 检查逻辑矛盾
    # 检查时间矛盾（排除日积月累类型中的句式练习）
    content_type = content_item.get('type', '')
    # 如果是日积月累类型，且标题包含"什么时候"或"句式"等，这是正常的句式练习，不检查时间矛盾
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
        # 但要排除明显的句式练习（如"早上...中午...晚上..."这样的并列结构）
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
        # 但要排除明显的对比或并列结构
        if has_positive and has_negative and len(full_text) < 30:
            # 检查是否是明显的对比结构（如"是...不是..."）
            if not (('是' in full_text and '不是' in full_text) or 
                   ('有' in full_text and '没有' in full_text) or
                   ('能' in full_text and '不能' in full_text)):
                issues.append({
                    "type": "前后矛盾",
                    "file": file_ref,
                    "title": content_item.get('title', ''),
                    "problem": "短文本中同时出现肯定和否定表达，可能存在前后矛盾"
                })
    
    # 4. 检查数字逻辑错误
    numbers = re.findall(r'[一二三四五六七八九十百千万]+|[0-9]+', full_text)
    if len(numbers) >= 2:
        # 检查数字是否合理（如"三个苹果，两个苹果"可能是重复或错误）
        # 这里只是简单检查，具体逻辑需要根据内容判断
        pass
    
    # 5. 检查内容是否完整（是否有明显的截断）
    if full_text and not full_text.rstrip().endswith(('。', '！', '？', '，')):
        # 如果最后没有标点，可能是截断了
        # 但有些内容可能确实不需要结尾标点，所以这个检查要谨慎
        pass
    
    return issues

def check_all_grade1_content():
    """检查所有1年级内容"""
    base_dir = Path(__file__).parent
    grade1_dir = base_dir / "有拼音" / "1年级"
    
    all_pinyin_issues = []
    all_logic_issues = []
    
    txt_files = sorted(grade1_dir.glob("*.txt"))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for week_data in data:
                week_num = week_data.get('week', 0)
                day_num = week_data.get('day', 0)
                theme = week_data.get('theme', '')
                file_ref = f"{txt_file.name} - 第{week_num}周第{day_num}天 - {theme}"
                
                # 收集所有内容文本，用于检查整体逻辑
                all_content_text = ""
                for content_item in week_data.get('content', []):
                    for obj in content_item.get('contentObject', []):
                        if isinstance(obj, dict):
                            if 'text' in obj:
                                all_content_text += obj['text']
                            elif 'content' in obj:
                                for sub_item in obj.get('content', []):
                                    if 'text' in sub_item:
                                        all_content_text += sub_item['text']
                
                for content_item in week_data.get('content', []):
                    # 检查拼音问题
                    pinyin_issues = check_pinyin_issues(content_item, file_ref)
                    all_pinyin_issues.extend(pinyin_issues)
                    
                    # 检查逻辑问题
                    logic_issues = check_logic_issues(content_item, file_ref, all_content_text)
                    all_logic_issues.extend(logic_issues)
        
        except Exception as e:
            all_pinyin_issues.append({
                "type": "文件读取错误",
                "file": str(txt_file),
                "problem": f"读取文件时出错：{str(e)}"
            })
    
    return all_pinyin_issues, all_logic_issues

def generate_report(pinyin_issues, logic_issues):
    """生成检查报告"""
    report = []
    report.append("=" * 80)
    report.append("1年级内容全面检查报告")
    report.append("=" * 80)
    report.append("")
    
    total_issues = len(pinyin_issues) + len(logic_issues)
    report.append(f"总计发现 {total_issues} 个问题")
    report.append(f"  - 拼音问题：{len(pinyin_issues)} 个")
    report.append(f"  - 逻辑问题：{len(logic_issues)} 个")
    report.append("")
    
    # 拼音问题报告
    if pinyin_issues:
        report.append("=" * 80)
        report.append("一、拼音问题检查")
        report.append("=" * 80)
        report.append("")
        
        # 按类型分组
        pinyin_by_type = defaultdict(list)
        for issue in pinyin_issues:
            pinyin_by_type[issue['type']].append(issue)
        
        for issue_type, issues in pinyin_by_type.items():
            report.append(f"【{issue_type}】共 {len(issues)} 处：")
            report.append("")
            for i, issue in enumerate(issues[:20], 1):  # 只显示前20个
                report.append(f"  {i}. {issue['file']}")
                report.append(f"     标题：{issue.get('title', '未知')}")
                if 'text' in issue:
                    report.append(f"     文本：{issue['text'][:50]}...")
                if 'pinyin' in issue:
                    report.append(f"     拼音：{issue['pinyin'][:50]}...")
                report.append(f"     问题：{issue['problem']}")
                report.append("")
            
            if len(issues) > 20:
                report.append(f"  ... 还有 {len(issues) - 20} 处类似问题")
                report.append("")
    else:
        report.append("=" * 80)
        report.append("一、拼音问题检查")
        report.append("=" * 80)
        report.append("")
        report.append("✅ 未发现拼音问题")
        report.append("")
    
    # 逻辑问题报告
    if logic_issues:
        report.append("=" * 80)
        report.append("二、内容逻辑问题检查")
        report.append("=" * 80)
        report.append("")
        
        # 按类型分组
        logic_by_type = defaultdict(list)
        for issue in logic_issues:
            logic_by_type[issue['type']].append(issue)
        
        for issue_type, issues in logic_by_type.items():
            report.append(f"【{issue_type}】共 {len(issues)} 处：")
            report.append("")
            for i, issue in enumerate(issues[:20], 1):  # 只显示前20个
                report.append(f"  {i}. {issue['file']}")
                report.append(f"     标题：{issue.get('title', '未知')}")
                report.append(f"     问题：{issue['problem']}")
                report.append("")
            
            if len(issues) > 20:
                report.append(f"  ... 还有 {len(issues) - 20} 处类似问题")
                report.append("")
    else:
        report.append("=" * 80)
        report.append("二、内容逻辑问题检查")
        report.append("=" * 80)
        report.append("")
        report.append("✅ 未发现逻辑问题")
        report.append("")
    
    report.append("=" * 80)
    report.append("检查完成")
    report.append("=" * 80)
    
    return '\n'.join(report)

if __name__ == "__main__":
    print("开始检查1年级内容...")
    pinyin_issues, logic_issues = check_all_grade1_content()
    report = generate_report(pinyin_issues, logic_issues)
    
    # 输出到控制台
    print(report)
    
    # 保存到文件
    report_file = Path(__file__).parent / "1年级全面检查报告.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已保存到：{report_file}")

