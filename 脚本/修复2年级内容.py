import os
import json
import re

def get_pinyin(text):
    """简单的拼音转换，这里只是占位，实际应该使用拼音库"""
    # 这个函数在实际应用中应该使用pypinyin等库
    # 这里我们只处理已有的拼音字段
    return ""

def fix_grade_2_content(base_path):
    grade_2_path = os.path.join(base_path, '有拼音', '2年级')
    
    if not os.path.exists(grade_2_path):
        print(f"错误：未找到2年级内容路径: {grade_2_path}")
        return
    
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
                        
                        # 修复缺少task和taskAnswer的日积月累
                        if item_type == "daily_accumulation":
                            if 'task' not in content_block or not content_block.get('task', '').strip():
                                # 根据内容类型生成合适的task
                                task = generate_task_for_daily_accumulation(content_block)
                                if task:
                                    content_block['task'] = task
                                    # 生成拼音（简化处理，实际应该用拼音库）
                                    content_block['taskPinyin'] = ""  # 需要手动补充或使用拼音库
                                    modified = True
                                    fixed_count += 1
                                    print(f"补充task: {filename} - {title}")
                            
                            if 'taskAnswer' not in content_block or not content_block.get('taskAnswer', '').strip():
                                # 根据task生成合适的taskAnswer
                                task = content_block.get('task', '')
                                task_answer = generate_task_answer_for_daily_accumulation(content_block, task)
                                if task_answer:
                                    content_block['taskAnswer'] = task_answer
                                    content_block['taskAnswerPinyin'] = ""  # 需要手动补充或使用拼音库
                                    modified = True
                                    fixed_count += 1
                                    print(f"补充taskAnswer: {filename} - {title}")
                        
                        # 修复缺少task的古诗
                        if item_type == "ancient_poem":
                            if 'task' not in content_block or not content_block.get('task', '').strip():
                                content_block['task'] = "记住这首诗，下次可以背给爸爸妈妈听。"
                                content_block['taskPinyin'] = "jì zhù zhè shǒu shī xià cì kě yǐ bèi gěi bà ba mā ma tīng"
                                if 'taskAnswer' not in content_block or not content_block.get('taskAnswer', '').strip():
                                    content_block['taskAnswer'] = "我已经记住了这首诗。"
                                    content_block['taskAnswerPinyin'] = "wǒ yǐ jīng jì zhù le zhè shǒu shī"
                                modified = True
                                fixed_count += 1
                                print(f"补充古诗task: {filename} - {title}")
                        
                        # 修复缺少task的课文
                        if item_type == "textbook_review":
                            if 'task' not in content_block or not content_block.get('task', '').strip():
                                # 根据课文内容生成合适的task
                                task = generate_task_for_textbook_review(content_block)
                                if task:
                                    content_block['task'] = task
                                    content_block['taskPinyin'] = ""  # 需要手动补充
                                    if 'taskAnswer' not in content_block or not content_block.get('taskAnswer', '').strip():
                                        content_block['taskAnswer'] = generate_task_answer_for_textbook_review(content_block, task)
                                        content_block['taskAnswerPinyin'] = ""
                                    modified = True
                                    fixed_count += 1
                                    print(f"补充课文task: {filename} - {title}")
                        
                        # 修复拼音不匹配问题
                        if 'contentObject' in content_block:
                            fixed_pinyin = fix_pinyin_mismatch(content_block)
                            if fixed_pinyin:
                                modified = True
                                fixed_count += fixed_pinyin
                                print(f"修复拼音: {filename} - {title} ({fixed_pinyin}处)")
                
                if modified:
                    # 保存文件
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(content, f, ensure_ascii=False, indent='\t')
                    print(f"已保存: {filename}")
                
            except json.JSONDecodeError as e:
                print(f"错误：文件 {filepath} JSON格式不正确: {e}")
            except Exception as e:
                print(f"错误：处理文件 {filepath} 时发生未知错误: {e}")
    
    print(f"\n总计修复 {fixed_count} 处问题")

def generate_task_for_daily_accumulation(content_block):
    """为日积月累生成合适的task"""
    content_object = content_block.get('contentObject', [])
    if not content_object:
        return ""
    
    first_item = content_object[0]
    title = first_item.get('title', '')
    content = first_item.get('content', [])
    
    # 根据子标题类型生成task
    if '好词' in title or '词语' in title:
        if content:
            # 取前两个词作为例子
            words = [item.get('text', '').strip() for item in content[:2] if item.get('text', '').strip()]
            if words:
                return f"用'{words[0]}'和'{words[1] if len(words) > 1 else words[0]}'各说一句话。"
        return "选择两个词语，各说一句话。"
    
    elif '好句' in title or '句子' in title:
        return "仿照例句，用学到的修辞手法说一句话。"
    
    elif '谚语' in title or '歇后语' in title:
        if content:
            first_text = content[0].get('text', '').split('。')[0].split('（')[0]
            return f"用'{first_text}'说一句话，鼓励自己。"
        return "选择一个谚语或歇后语，用它说一句话。"
    
    elif '修辞' in title or '比喻' in title or '拟人' in title or '夸张' in title:
        return "仿照例句，用学到的修辞手法说一句话。"
    
    elif '写话' in title or '锦囊' in title:
        return "用学到的写话方法，说一句话。"
    
    else:
        # 默认task
        return "认真读一读，试着用学到的内容说一句话。"

def generate_task_answer_for_daily_accumulation(content_block, task):
    """为日积月累生成合适的taskAnswer"""
    if not task:
        return ""
    
    content_object = content_block.get('contentObject', [])
    if not content_object:
        return "我已经完成了任务。"
    
    first_item = content_object[0]
    content = first_item.get('content', [])
    
    # 根据task内容生成答案
    if '词语' in task or '词' in task:
        if content:
            word = content[0].get('text', '').strip()
            return f"我用'{word}'说了一句话。"
        return "我已经用词语说了句子。"
    
    elif '修辞' in task or '比喻' in task or '拟人' in task:
        return "我已经用学到的修辞手法说了一句话。"
    
    elif '谚语' in task or '歇后语' in task:
        if content:
            first_text = content[0].get('text', '').split('。')[0].split('（')[0]
            return f"我用'{first_text}'说了一句话，鼓励自己。"
        return "我已经用谚语说了一句话。"
    
    else:
        return "我已经完成了任务。"

def generate_task_for_textbook_review(content_block):
    """为课文生成合适的task"""
    content_object = content_block.get('contentObject', [])
    if not content_object:
        return ""
    
    # 获取前几句内容
    first_texts = [obj.get('text', '') for obj in content_object[:3]]
    full_text = ''.join(first_texts)
    
    # 根据内容特点生成task
    if '说' in full_text or '告诉' in full_text:
        return "如果你是文中的角色，你会说什么？"
    elif '做' in full_text or '想' in full_text:
        return "如果你是文中的角色，你会怎么做？"
    elif '？' in full_text or '?' in full_text:
        return "读完这个故事，你有什么想法？"
    else:
        return "读完这个故事，你有什么感受？"

def generate_task_answer_for_textbook_review(content_block, task):
    """为课文生成合适的taskAnswer"""
    if not task:
        return ""
    
    if '说' in task:
        return "我会说一些鼓励和赞美的话。"
    elif '做' in task:
        return "我会像文中的角色一样，帮助别人。"
    elif '想法' in task or '感受' in task:
        return "我觉得这个故事很有趣，我学到了很多。"
    else:
        return "我已经完成了任务。"

def fix_pinyin_mismatch(content_block):
    """修复拼音不匹配问题"""
    fixed_count = 0
    content_object = content_block.get('contentObject', [])
    item_type = content_block.get('type', '')
    
    # 处理日积月累的嵌套结构
    if item_type == "daily_accumulation":
        for obj in content_object:
            if 'content' in obj:
                for sub_obj in obj['content']:
                    pinyin = sub_obj.get('pinyin', '')
                    text = sub_obj.get('text', '')
                    # 计算拼音音节数和汉字数
                    pinyin_syllables = len([s for s in pinyin.split() if s]) if pinyin else 0
                    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
                    
                    # 如果差异较大（超过2个），可能需要修复
                    # 但这里我们只标记，不自动修复，因为需要人工判断
                    if abs(pinyin_syllables - chinese_chars) > 2:
                        # 这里可以记录问题，但不自动修复
                        pass
    else:
        # 处理普通内容
        for obj in content_object:
            pinyin = obj.get('pinyin', '')
            text = obj.get('text', '')
            pinyin_syllables = len([s for s in pinyin.split() if s]) if pinyin else 0
            chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            
            # 如果差异较大，记录但不自动修复
            if abs(pinyin_syllables - chinese_chars) > 2:
                pass
    
    return fixed_count

if __name__ == "__main__":
    base_directory = '/Users/trl_1/Downloads/0616/edu/晨读/morning_read_txt/内容'
    print("开始修复2年级内容...")
    print("=" * 60)
    fix_grade_2_content(base_directory)
    print("=" * 60)
    print("修复完成！")

