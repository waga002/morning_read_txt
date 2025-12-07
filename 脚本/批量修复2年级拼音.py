import os
import json
import re

def remove_punctuation_from_pinyin(pinyin):
    """移除拼音中的标点符号，并确保拼音之间有正确的空格"""
    # 移除所有标点符号
    pinyin = re.sub(r'[，。！？、：；""''（）【】《》]', ' ', pinyin)
    # 规范化空格：多个空格合并为一个，去除首尾空格
    pinyin = re.sub(r'\s+', ' ', pinyin).strip()
    return pinyin

def fix_pinyin_mismatches(base_path):
    """修复2年级内容中的拼音不匹配问题"""
    grade_2_path = os.path.join(base_path, '有拼音', '2年级')
    
    if not os.path.exists(grade_2_path):
        print(f"错误：未找到2年级内容路径: {grade_2_path}")
        return
    
    fixed_count = 0
    issues_found = []
    
    for filename in os.listdir(grade_2_path):
        if filename.endswith('.txt'):
            filepath = os.path.join(grade_2_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                
                modified = False
                
                for item in content:
                    week = item.get('week')
                    day = item.get('day')
                    theme = item.get('theme', '未知主题')
                    
                    for content_block in item.get('content', []):
                        title = content_block.get('title', '')
                        item_type = content_block.get('type', '')
                        
                        # 处理普通内容
                        if 'contentObject' in content_block:
                            for obj in content_block['contentObject']:
                                pinyin = obj.get('pinyin', '')
                                text = obj.get('text', '')
                                
                                # 移除拼音中的标点符号
                                original_pinyin = pinyin
                                pinyin = remove_punctuation_from_pinyin(pinyin)
                                
                                if pinyin != original_pinyin:
                                    obj['pinyin'] = pinyin
                                    modified = True
                                    fixed_count += 1
                                    print(f"移除标点: {filename} - {title}\n  原文: {text}\n  原拼音: {original_pinyin}\n  新拼音: {pinyin}")
                                
                                # 计算拼音音节数和汉字数
                                pinyin_syllables = len([s for s in pinyin.split() if s]) if pinyin else 0
                                chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff' and not c.isdigit()])
                                
                                # 如果差异较大，记录问题
                                diff = abs(pinyin_syllables - chinese_chars)
                                if diff > 2 and pinyin_syllables > 0 and chinese_chars > 0:
                                    issues_found.append({
                                        'file': filename,
                                        'week': week,
                                        'day': day,
                                        'theme': theme,
                                        'title': title,
                                        'text': text,
                                        'pinyin': pinyin,
                                        'pinyin_count': pinyin_syllables,
                                        'char_count': chinese_chars,
                                        'obj': obj
                                    })
                        
                        # 处理日积月累的嵌套结构
                        if item_type == "daily_accumulation":
                            for obj in content_block.get('contentObject', []):
                                if 'content' in obj:
                                    for sub_obj in obj['content']:
                                        pinyin = sub_obj.get('pinyin', '')
                                        text = sub_obj.get('text', '')
                                        
                                        # 移除拼音中的标点符号
                                        original_pinyin = pinyin
                                        pinyin = remove_punctuation_from_pinyin(pinyin)
                                        
                                        if pinyin != original_pinyin:
                                            sub_obj['pinyin'] = pinyin
                                            modified = True
                                            fixed_count += 1
                                            print(f"移除标点: {filename} - {title} - {obj.get('title', '')}\n  原文: {text}\n  原拼音: {original_pinyin}\n  新拼音: {pinyin}")
                                        
                                        # 计算拼音音节数和汉字数
                                        pinyin_syllables = len([s for s in pinyin.split() if s]) if pinyin else 0
                                        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff' and not c.isdigit()])
                                        
                                        # 如果差异较大，记录问题
                                        diff = abs(pinyin_syllables - chinese_chars)
                                        if diff > 2 and pinyin_syllables > 0 and chinese_chars > 0:
                                            issues_found.append({
                                                'file': filename,
                                                'week': week,
                                                'day': day,
                                                'theme': theme,
                                                'title': title,
                                                'subtitle': obj.get('title', ''),
                                                'text': text,
                                                'pinyin': pinyin,
                                                'pinyin_count': pinyin_syllables,
                                                'char_count': chinese_chars,
                                                'obj': sub_obj
                                            })
                
                if modified:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(content, f, ensure_ascii=False, indent='\t')
                    print(f"已保存: {filename}\n")
                
            except json.JSONDecodeError as e:
                print(f"错误：文件 {filepath} JSON格式不正确: {e}")
            except Exception as e:
                print(f"错误：处理文件 {filepath} 时发生未知错误: {e}")
    
    print(f"\n总计移除标点符号 {fixed_count} 处")
    print(f"发现需要修复的拼音不匹配问题 {len(issues_found)} 处")
    
    # 输出需要手动修复的问题
    if issues_found:
        print("\n需要手动修复的问题：")
        for issue in issues_found[:20]:  # 只显示前20个
            print(f"\n{issue['file']} - 第{issue['week']}周第{issue['day']}天 - {issue['theme']}")
            print(f"  标题：{issue['title']}")
            if 'subtitle' in issue:
                print(f"  子标题：{issue['subtitle']}")
            print(f"  文字：{issue['text']}")
            print(f"  拼音：{issue['pinyin']}")
            print(f"  拼音音节数：{issue['pinyin_count']}，汉字数：{issue['char_count']}")

if __name__ == "__main__":
    base_directory = '/Users/trl_1/Downloads/0616/edu/晨读/morning_read_txt/内容'
    print("开始修复2年级拼音问题（移除标点符号）...")
    print("=" * 60)
    fix_pinyin_mismatches(base_directory)
    print("=" * 60)
    print("修复完成！")

