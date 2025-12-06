import os
import json
import re

def remove_punctuation_from_pinyin(pinyin):
    """移除拼音中的标点符号，并确保拼音之间有正确的空格"""
    if not pinyin:
        return ""
    # 移除所有标点符号，替换为空格
    pinyin = re.sub(r'[，。！？、：；""''（）【】《》]', ' ', pinyin)
    # 规范化空格：多个空格合并为一个，去除首尾空格
    pinyin = re.sub(r'\s+', ' ', pinyin).strip()
    return pinyin

def fix_missing_spaces(pinyin):
    """修复拼音中缺少空格的问题"""
    if not pinyin:
        return ""
    # 如果拼音中没有空格，可能是格式问题，暂时不处理
    # 这里主要处理标点符号移除后缺少空格的情况
    return pinyin

def fix_pinyin_mismatches(base_path):
    """修复2年级内容中的拼音不匹配问题"""
    grade_2_path = os.path.join(base_path, '有拼音', '2年级')
    
    if not os.path.exists(grade_2_path):
        print(f"错误：未找到2年级内容路径: {grade_2_path}")
        return
    
    fixed_count = 0
    
    # 读取检查报告，获取所有需要修复的问题
    report_file = os.path.join(base_path, '2年级内容检查报告.md')
    issues = []
    
    # 先移除所有拼音中的标点符号
    for filename in os.listdir(grade_2_path):
        if filename.endswith('.txt'):
            filepath = os.path.join(grade_2_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                
                modified = False
                
                for item in content:
                    for content_block in item.get('content', []):
                        title = content_block.get('title', '')
                        item_type = content_block.get('type', '')
                        
                        # 处理普通内容
                        if 'contentObject' in content_block:
                            for obj in content_block['contentObject']:
                                pinyin = obj.get('pinyin', '')
                                if pinyin:
                                    new_pinyin = remove_punctuation_from_pinyin(pinyin)
                                    if new_pinyin != pinyin:
                                        obj['pinyin'] = new_pinyin
                                        modified = True
                                        fixed_count += 1
                        
                        # 处理日积月累的嵌套结构
                        if item_type == "daily_accumulation":
                            for obj in content_block.get('contentObject', []):
                                if 'content' in obj:
                                    for sub_obj in obj['content']:
                                        pinyin = sub_obj.get('pinyin', '')
                                        if pinyin:
                                            new_pinyin = remove_punctuation_from_pinyin(pinyin)
                                            if new_pinyin != pinyin:
                                                sub_obj['pinyin'] = new_pinyin
                                                modified = True
                                                fixed_count += 1
                
                if modified:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(content, f, ensure_ascii=False, indent='\t')
                    print(f"已移除标点: {filename} ({fixed_count}处)")
                    fixed_count = 0
                
            except Exception as e:
                print(f"错误：处理文件 {filepath} 时发生错误: {e}")
    
    print(f"\n总计移除标点符号完成")

if __name__ == "__main__":
    base_directory = '/Users/trl_1/Downloads/0616/edu/晨读/morning_read_txt/内容'
    print("开始修复2年级拼音问题（移除标点符号）...")
    print("=" * 60)
    fix_pinyin_mismatches(base_directory)
    print("=" * 60)
    print("修复完成！")

