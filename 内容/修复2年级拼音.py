import os
import json
import re

def fix_pinyin_mismatches(base_path):
    """修复2年级内容中的拼音不匹配问题"""
    grade_2_path = os.path.join(base_path, '有拼音', '2年级')
    
    if not os.path.exists(grade_2_path):
        print(f"错误：未找到2年级内容路径: {grade_2_path}")
        return
    
    # 已知的拼音修复规则
    pinyin_fixes = {
        # 文件: 行号或内容标识 -> 修复后的拼音
    }
    
    fixed_count = 0
    
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
                                text = obj.get('text', '')
                                
                                # 计算拼音音节数和汉字数
                                pinyin_syllables = len([s for s in pinyin.split() if s]) if pinyin else 0
                                chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
                                
                                # 如果差异超过2，尝试修复
                                diff = pinyin_syllables - chinese_chars
                                
                                if abs(diff) > 2 and pinyin and text:
                                    # 尝试根据常见错误模式修复
                                    fixed_pinyin = try_fix_pinyin(pinyin, text, diff)
                                    if fixed_pinyin and fixed_pinyin != pinyin:
                                        obj['pinyin'] = fixed_pinyin
                                        modified = True
                                        fixed_count += 1
                                        print(f"修复: {filename} - {title}\n  原文: {text}\n  原拼音: {pinyin}\n  新拼音: {fixed_pinyin}")
                        
                        # 处理日积月累的嵌套结构
                        if item_type == "daily_accumulation":
                            for obj in content_block.get('contentObject', []):
                                if 'content' in obj:
                                    for sub_obj in obj['content']:
                                        pinyin = sub_obj.get('pinyin', '')
                                        text = sub_obj.get('text', '')
                                        
                                        pinyin_syllables = len([s for s in pinyin.split() if s]) if pinyin else 0
                                        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
                                        
                                        diff = pinyin_syllables - chinese_chars
                                        
                                        if abs(diff) > 2 and pinyin and text:
                                            fixed_pinyin = try_fix_pinyin(pinyin, text, diff)
                                            if fixed_pinyin and fixed_pinyin != pinyin:
                                                sub_obj['pinyin'] = fixed_pinyin
                                                modified = True
                                                fixed_count += 1
                                                print(f"修复: {filename} - {title} - {obj.get('title', '')}\n  原文: {text}\n  原拼音: {pinyin}\n  新拼音: {fixed_pinyin}")
                
                if modified:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(content, f, ensure_ascii=False, indent='\t')
                    print(f"已保存: {filename}\n")
                
            except json.JSONDecodeError as e:
                print(f"错误：文件 {filepath} JSON格式不正确: {e}")
            except Exception as e:
                print(f"错误：处理文件 {filepath} 时发生未知错误: {e}")
    
    print(f"\n总计修复 {fixed_count} 处拼音不匹配问题")

def try_fix_pinyin(pinyin, text, diff):
    """尝试修复拼音，基于常见错误模式"""
    # 移除标点符号后的文本
    clean_text = re.sub(r'[，。！？、：；""''（）【】《》]', '', text)
    chinese_chars = [c for c in clean_text if '\u4e00' <= c <= '\u9fff']
    chinese_count = len(chinese_chars)
    
    pinyin_parts = [s for s in pinyin.split() if s]
    pinyin_count = len(pinyin_parts)
    
    # 如果拼音比汉字少，可能是缺少了某些音节
    if pinyin_count < chinese_count:
        # 尝试在常见位置补充
        # 这里需要更智能的算法，暂时返回None让人工处理
        return None
    
    # 如果拼音比汉字多，可能是多了某些音节
    elif pinyin_count > chinese_count:
        # 检查是否有重复的音节
        # 检查是否有语气词（如"呀"、"啊"等）在拼音中但不在文字中
        # 这里也需要更智能的算法
        return None
    
    return None

if __name__ == "__main__":
    base_directory = '/Users/trl_1/Downloads/0616/edu/晨读/morning_read_txt/内容'
    print("开始修复2年级拼音不匹配问题...")
    print("=" * 60)
    fix_pinyin_mismatches(base_directory)
    print("=" * 60)
    print("修复完成！")

