#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面修复2年级内容中的拼音问题：
1. 移除拼音中的标点符号
2. 修复拼音与汉字不匹配的问题（使用pypinyin库）
3. 数字不要生成拼音（只对汉字生成拼音）
"""
import os
import json
import re
from pathlib import Path

try:
    from pypinyin import lazy_pinyin, Style
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False
    print("警告：未安装pypinyin库，将无法自动补充拼音。请运行: pip install pypinyin")

def remove_punctuation_from_pinyin(pinyin):
    """移除拼音中的标点符号，并确保拼音之间有正确的空格"""
    if not pinyin:
        return ""
    # 移除所有标点符号，替换为空格
    pinyin = re.sub(r'[，。！？、：；""''（）【】《》〈〉『』「」]', ' ', pinyin)
    # 规范化空格：多个空格合并为一个，去除首尾空格
    pinyin = re.sub(r'\s+', ' ', pinyin).strip()
    return pinyin

def get_pinyin_for_text(text, with_tone=True):
    """获取文本的拼音（仅汉字，不包括数字）"""
    if not HAS_PYPINYIN:
        return None
    
    # 只提取汉字（不包括数字、字母、标点符号）
    chinese_chars = ''.join(re.findall(r'[\u4e00-\u9fff]', text))
    if not chinese_chars:
        return None
    
    # 获取拼音，使用带声调的格式（默认）
    if with_tone:
        pinyin_list = lazy_pinyin(chinese_chars, style=Style.TONE)
    else:
        pinyin_list = lazy_pinyin(chinese_chars, style=Style.NORMAL)
    return ' '.join(pinyin_list)

def count_chinese_chars(text):
    """统计文本中的汉字数量（不包括数字、字母、标点）"""
    return len(re.findall(r'[\u4e00-\u9fff]', text))

def count_pinyin_syllables(pinyin):
    """统计拼音音节数量"""
    if not pinyin:
        return 0
    # 移除标点后统计
    cleaned = remove_punctuation_from_pinyin(pinyin)
    return len([s for s in cleaned.split() if s.strip()])

def fix_pinyin_for_item(obj, text_key='text', pinyin_key='pinyin'):
    """修复单个项目的拼音"""
    if not isinstance(obj, dict):
        return False
    
    text = obj.get(text_key, '')
    original_pinyin = obj.get(pinyin_key, '')
    
    if not text:
        return False
    
    fixed = False
    
    # 1. 移除拼音中的标点符号
    cleaned_pinyin = remove_punctuation_from_pinyin(original_pinyin)
    if cleaned_pinyin != original_pinyin:
        obj[pinyin_key] = cleaned_pinyin
        fixed = True
    
    # 2. 检查拼音是否完整（只针对汉字）
    chinese_chars = ''.join(re.findall(r'[\u4e00-\u9fff]', text))
    if chinese_chars:
        char_count = len(chinese_chars)
        pinyin_syllables = count_pinyin_syllables(cleaned_pinyin)
        
        # 2.1 检查拼音是否过多（可能是重复或包含了数字的拼音）
        if pinyin_syllables > char_count * 1.2 and char_count > 3:
            # 尝试获取完整拼音（只针对汉字）
            full_pinyin_tone = get_pinyin_for_text(text, with_tone=True)
            if full_pinyin_tone:
                full_syllables = len(full_pinyin_tone.split())
                # 如果完整拼音明显少于现有拼音，说明现有拼音可能有重复或包含了数字拼音
                if full_syllables < pinyin_syllables * 0.9:
                    # 使用完整拼音（只针对汉字）
                    obj[pinyin_key] = full_pinyin_tone
                    fixed = True
                    return fixed
        
        # 2.2 如果拼音比汉字少很多，尝试补充（降低阈值以修复更多问题）
        if pinyin_syllables < char_count * 0.9 and char_count > 3:
            # 尝试获取完整拼音（只针对汉字）
            full_pinyin_tone = get_pinyin_for_text(text, with_tone=True)
            
            if full_pinyin_tone:
                full_syllables = len(full_pinyin_tone.split())
                if full_syllables > pinyin_syllables:
                    existing_parts = cleaned_pinyin.split()
                    full_parts_tone = full_pinyin_tone.split()
                    
                    # 移除声调的辅助函数
                    def remove_tone(pinyin_str):
                        tone_map = {
                            'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
                            'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
                            'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
                            'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
                            'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
                            'ǖ': 'ü', 'ǘ': 'ü', 'ǚ': 'ü', 'ǜ': 'ü'
                        }
                        result = ''
                        for char in pinyin_str.lower():
                            result += tone_map.get(char, char)
                        return result
                    
                    is_prefix = True
                    is_suffix = False
                    is_substring = False
                    
                    # 检查是否是前缀
                    for i, part in enumerate(existing_parts):
                        part_no_tone = remove_tone(part)
                        if i >= len(full_parts_tone):
                            is_prefix = False
                            break
                        full_part_no_tone = remove_tone(full_parts_tone[i])
                        if part_no_tone != full_part_no_tone:
                            is_prefix = False
                            break
                    
                    # 检查是否是后缀
                    if not is_prefix and len(existing_parts) > 0:
                        existing_no_tone = [remove_tone(p) for p in existing_parts]
                        full_no_tone = [remove_tone(p) for p in full_parts_tone]
                        
                        if len(existing_no_tone) <= len(full_no_tone):
                            suffix_match = True
                            for i, part in enumerate(existing_no_tone):
                                idx = len(full_no_tone) - len(existing_no_tone) + i
                                if idx < 0 or part != full_no_tone[idx]:
                                    suffix_match = False
                                    break
                            if suffix_match:
                                is_suffix = True
                        
                        # 检查是否是中间部分（子串）
                        existing_str = ' '.join(existing_no_tone)
                        full_str = ' '.join(full_no_tone)
                        if existing_str in full_str:
                            is_substring = True
                    
                    # 如果现有拼音是完整拼音的前缀、后缀或子串，且明显不完整，使用完整拼音
                    if (is_prefix or is_suffix or is_substring) and len(existing_parts) > 0:
                        if is_prefix and pinyin_syllables < full_syllables:
                            obj[pinyin_key] = full_pinyin_tone
                            fixed = True
                        elif (is_suffix or is_substring) and pinyin_syllables < char_count * 0.8:
                            obj[pinyin_key] = full_pinyin_tone
                            fixed = True
                    elif len(existing_parts) == 0 or pinyin_syllables == 0:
                        # 如果拼音完全缺失，使用完整拼音
                        obj[pinyin_key] = full_pinyin_tone
                        fixed = True
                    elif pinyin_syllables < char_count * 0.5:
                        # 如果拼音数量少于汉字数量的一半，说明拼音严重不完整，使用完整拼音
                        obj[pinyin_key] = full_pinyin_tone
                        fixed = True
                    elif abs(pinyin_syllables - char_count) > max(2, char_count * 0.2):
                        # 如果差异较大（超过20%或超过2个），且不是前缀/后缀/子串关系，直接使用完整拼音
                        obj[pinyin_key] = full_pinyin_tone
                        fixed = True
        # 2.3 如果拼音数量与汉字数量差异较大，且拼音明显不匹配，重新生成
        elif abs(pinyin_syllables - char_count) > max(1, char_count * 0.15) and char_count > 3:
            # 重新生成拼音（只针对汉字）
            full_pinyin_tone = get_pinyin_for_text(text, with_tone=True)
            if full_pinyin_tone:
                obj[pinyin_key] = full_pinyin_tone
                fixed = True
    
    return fixed

def fix_grade2_pinyin():
    """修复2年级所有文件的拼音问题"""
    base_dir = Path(__file__).parent
    grade2_dir = base_dir / "有拼音" / "2年级"
    
    if not grade2_dir.exists():
        print(f"错误：未找到2年级内容路径: {grade2_dir}")
        return
    
    total_fixed = 0
    files_modified = []
    
    txt_files = sorted(grade2_dir.glob("*.txt"))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_fixed = False
            
            for week_data in data:
                week_num = week_data.get('week', 0)
                day_num = week_data.get('day', 0)
                theme = week_data.get('theme', '')
                
                for content_item in week_data.get('content', []):
                    title = content_item.get('title', '')
                    
                    # 修复contentObject中的拼音
                    for obj in content_item.get('contentObject', []):
                        if isinstance(obj, dict):
                            # 检查是否有直接的text和pinyin
                            if 'text' in obj and 'pinyin' in obj:
                                original_pinyin = obj['pinyin']
                                if fix_pinyin_for_item(obj):
                                    file_fixed = True
                                    total_fixed += 1
                                    print(f"修复: {txt_file.name} - 第{week_num}周第{day_num}天 - {theme}")
                                    print(f"  标题: {title}")
                                    print(f"  文本: {obj['text'][:60]}")
                                    print(f"  原拼音: {original_pinyin[:60]}")
                                    print(f"  新拼音: {obj['pinyin'][:60]}")
                                    print()
                            
                            # 检查嵌套的content（日积月累类型）
                            elif 'content' in obj:
                                for sub_item in obj.get('content', []):
                                    if isinstance(sub_item, dict) and 'text' in sub_item and 'pinyin' in sub_item:
                                        original_pinyin = sub_item['pinyin']
                                        if fix_pinyin_for_item(sub_item):
                                            file_fixed = True
                                            total_fixed += 1
                                            print(f"修复: {txt_file.name} - 第{week_num}周第{day_num}天 - {theme}")
                                            print(f"  标题: {title} - {obj.get('title', '')}")
                                            print(f"  文本: {sub_item['text'][:60]}")
                                            print(f"  原拼音: {original_pinyin[:60]}")
                                            print(f"  新拼音: {sub_item['pinyin'][:60]}")
                                            print()
                    
                    # 修复taskPinyin
                    if 'taskPinyin' in content_item and content_item['taskPinyin']:
                        task_pinyin = content_item['taskPinyin']
                        cleaned = remove_punctuation_from_pinyin(task_pinyin)
                        
                        # 检查是否需要重新生成（只针对汉字）
                        task_text = content_item.get('task', '')
                        if task_text:
                            chinese_chars = ''.join(re.findall(r'[\u4e00-\u9fff]', task_text))
                            if chinese_chars:
                                char_count = len(chinese_chars)
                                pinyin_syllables = count_pinyin_syllables(cleaned)
                                if abs(pinyin_syllables - char_count) > max(2, char_count * 0.2) and char_count > 3:
                                    full_pinyin = get_pinyin_for_text(task_text, with_tone=True)
                                    if full_pinyin:
                                        cleaned = full_pinyin
                        
                        if cleaned != task_pinyin:
                            content_item['taskPinyin'] = cleaned
                            file_fixed = True
                            total_fixed += 1
                            print(f"修复taskPinyin: {txt_file.name} - 第{week_num}周第{day_num}天 - {theme}")
                            print(f"  标题: {title}")
                            print(f"  原拼音: {task_pinyin[:60]}")
                            print(f"  新拼音: {cleaned[:60]}")
                            print()
                    
                    # 修复taskAnswerPinyin
                    if 'taskAnswerPinyin' in content_item and content_item['taskAnswerPinyin']:
                        answer_pinyin = content_item['taskAnswerPinyin']
                        cleaned = remove_punctuation_from_pinyin(answer_pinyin)
                        
                        # 检查是否需要重新生成（只针对汉字）
                        answer_text = content_item.get('taskAnswer', '')
                        if answer_text:
                            chinese_chars = ''.join(re.findall(r'[\u4e00-\u9fff]', answer_text))
                            if chinese_chars:
                                char_count = len(chinese_chars)
                                pinyin_syllables = count_pinyin_syllables(cleaned)
                                if abs(pinyin_syllables - char_count) > max(2, char_count * 0.2) and char_count > 3:
                                    full_pinyin = get_pinyin_for_text(answer_text, with_tone=True)
                                    if full_pinyin:
                                        cleaned = full_pinyin
                        
                        if cleaned != answer_pinyin:
                            content_item['taskAnswerPinyin'] = cleaned
                            file_fixed = True
                            total_fixed += 1
                            print(f"修复taskAnswerPinyin: {txt_file.name} - 第{week_num}周第{day_num}天 - {theme}")
                            print(f"  标题: {title}")
                            print(f"  原拼音: {answer_pinyin[:60]}")
                            print(f"  新拼音: {cleaned[:60]}")
                            print()
                    
                    # 修复其他拼音字段
                    pinyin_fields = ['titlePinyin', 'authorPinyin', 'dynastyPinyin', 'annotationPinyin', 'translationPinyin']
                    for field in pinyin_fields:
                        if field in content_item and content_item[field]:
                            field_pinyin = content_item[field]
                            cleaned = remove_punctuation_from_pinyin(field_pinyin)
                            
                            # 对于titlePinyin，也检查是否需要重新生成
                            if field == 'titlePinyin':
                                title_text = content_item.get('title', '')
                                if title_text:
                                    chinese_chars = ''.join(re.findall(r'[\u4e00-\u9fff]', title_text))
                                    if chinese_chars:
                                        char_count = len(chinese_chars)
                                        pinyin_syllables = count_pinyin_syllables(cleaned)
                                        if abs(pinyin_syllables - char_count) > max(2, char_count * 0.2) and char_count > 3:
                                            full_pinyin = get_pinyin_for_text(title_text, with_tone=True)
                                            if full_pinyin:
                                                cleaned = full_pinyin
                            
                            if cleaned != field_pinyin:
                                content_item[field] = cleaned
                                file_fixed = True
                                total_fixed += 1
                                print(f"修复{field}: {txt_file.name} - 第{week_num}周第{day_num}天 - {theme}")
                                print(f"  标题: {title}")
                                print(f"  原拼音: {field_pinyin[:60]}")
                                print(f"  新拼音: {cleaned[:60]}")
                                print()
            
            # 保存修改
            if file_fixed:
                with open(txt_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent='\t')
                files_modified.append(txt_file.name)
                print(f"已保存: {txt_file.name}\n")
        
        except Exception as e:
            print(f"处理文件 {txt_file.name} 时出错: {str(e)}\n")
    
    print("=" * 80)
    print("修复完成")
    print("=" * 80)
    print(f"总计修复 {total_fixed} 处拼音问题")
    print(f"修改了 {len(files_modified)} 个文件:")
    for filename in files_modified:
        print(f"  - {filename}")

if __name__ == "__main__":
    print("开始修复2年级拼音问题...")
    print("=" * 80)
    if not HAS_PYPINYIN:
        print("警告：未安装pypinyin库，将只能移除标点符号，无法自动补充拼音。")
        print("请运行: pip install pypinyin")
        print()
    fix_grade2_pinyin()
