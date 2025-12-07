import os
import json
import re

def check_grade_2_content(base_path):
    report = []
    grade_2_path = os.path.join(base_path, '有拼音', '2年级')
    
    if not os.path.exists(grade_2_path):
        report.append(f"错误：未找到2年级内容路径: {grade_2_path}")
        return report

    for filename in os.listdir(grade_2_path):
        if filename.endswith('.txt'):
            filepath = os.path.join(grade_2_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    
                for item in content:
                    grade = item.get('grade')
                    term = item.get('term')
                    week = item.get('week')
                    day = item.get('day')
                    theme = item.get('theme', '未知主题')

                    for content_block in item.get('content', []):
                        title = content_block.get('title', '未知标题')
                        item_type = content_block.get('type', '未知类型')

                        # 检查 task 字段
                        if 'task' not in content_block or not content_block['task'].strip():
                            report.append(f"【缺少task字段】 - {filename} - 第{week}周第{day}天 - {theme}\n    标题：{title} (类型：{item_type})")
                        
                        # 检查 taskAnswer 字段
                        if 'taskAnswer' not in content_block or not content_block['taskAnswer'].strip():
                            report.append(f"【缺少taskAnswer字段】 - {filename} - 第{week}周第{day}天 - {theme}\n    标题：{title} (类型：{item_type})")

                        # 检查 contentObject 中的拼音和文字匹配
                        if 'contentObject' in content_block:
                            for obj in content_block['contentObject']:
                                pinyin = obj.get('pinyin', '')
                                text = obj.get('text', '')
                                
                                # 排除 "日积月累" 类型下的 "content" 数组，因为其结构不同
                                if item_type == "daily_accumulation" and "content" in obj:
                                    for sub_obj in obj["content"]:
                                        sub_pinyin = sub_obj.get('pinyin', '')
                                        sub_text = sub_obj.get('text', '')
                                        # 计算拼音音节数（按空格分割）
                                        pinyin_syllables = len([s for s in sub_pinyin.split() if s]) if sub_pinyin else 0
                                        # 计算汉字数（排除标点符号和数字）
                                        chinese_chars = len([c for c in sub_text if '\u4e00' <= c <= '\u9fff' and not c.isdigit()])
                                        if pinyin_syllables != chinese_chars and pinyin_syllables > 0 and chinese_chars > 0:
                                            report.append(f"【拼音可能不匹配】 - {filename} - 第{week}周第{day}天 - {theme}\n    标题：{title}\n    子标题：{obj.get('title', '未知子标题')}\n    文字：{sub_text}\n    拼音：{sub_pinyin}\n    拼音音节数：{pinyin_syllables}，汉字数：{chinese_chars}")
                                    continue # 跳过外层contentObject的检查

                                # 计算拼音音节数（按空格分割）
                                pinyin_syllables = len([s for s in pinyin.split() if s]) if pinyin else 0
                                # 计算汉字数（排除标点符号和数字）
                                chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff' and not c.isdigit()])
                                if pinyin_syllables != chinese_chars and pinyin_syllables > 0 and chinese_chars > 0:
                                    report.append(f"【拼音可能不匹配】 - {filename} - 第{week}周第{day}天 - {theme}\n    标题：{title}\n    文字：{text}\n    拼音：{pinyin}\n    拼音音节数：{pinyin_syllables}，汉字数：{chinese_chars}")

            except json.JSONDecodeError as e:
                report.append(f"错误：文件 {filepath} JSON格式不正确: {e}")
            except Exception as e:
                report.append(f"错误：处理文件 {filepath} 时发生未知错误: {e}")
    return report

def check_grade_2_logic_issues(base_path):
    report = []
    grade_2_path = os.path.join(base_path, '有拼音', '2年级')
    
    if not os.path.exists(grade_2_path):
        report.append(f"错误：未找到2年级内容路径: {grade_2_path}")
        return report

    # 常见错别字和表达错误
    common_typos = {
        "看玩": "看完",
        "迷语": "谜语",
        "雨运": "雨来",
        "还着": "还有",
        "弯鹅": "坡上鹅",
        "汪汪大笑": "汪汪叫",
    }

    for filename in os.listdir(grade_2_path):
        if filename.endswith('.txt'):
            filepath = os.path.join(grade_2_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    
                for item in content:
                    grade = item.get('grade')
                    term = item.get('term')
                    week = item.get('week')
                    day = item.get('day')
                    theme = item.get('theme', '未知主题')

                    for content_block in item.get('content', []):
                        title = content_block.get('title', '未知标题')
                        item_type = content_block.get('type', '未知类型')

                        # 检查错别字
                        if 'contentObject' in content_block:
                            for obj in content_block['contentObject']:
                                text = obj.get('text', '')
                                for typo, correct in common_typos.items():
                                    if typo in text:
                                        report.append(f"【错别字/表达错误】 - {filename} - 第{week}周第{day}天 - {theme}\n    标题：{title}\n    错误：`\"text\":\"{text}\"`\n    建议：应为`\"text\":\"{text.replace(typo, correct)}\"`")

                        # 检查绕口令长度
                        if item_type == "tongue_twisters":
                            if 'contentObject' in content_block:
                                if len(content_block['contentObject']) < 4:
                                    report.append(f"【内容拼凑/不连贯】 - {filename} - 第{week}周第{day}天 - {theme}\n    标题：{title}\n    绕口令内容过短，可能不够绕口")
                        
                        # 检查不当词汇或表达（对2年级来说）
                        if 'contentObject' in content_block:
                            for obj in content_block['contentObject']:
                                if 'text' in obj:
                                    text = obj['text']
                                    # 检查是否有过于复杂的表达
                                    if len(text) > 30 and item_type == "daily_accumulation":
                                        # 检查是否包含过于复杂的词汇
                                        complex_words = ["经验丰富", "耐心地", "巨大的", "广阔的", "缓缓", "善良的"]
                                        if any(word in text for word in complex_words):
                                            report.append(f"【难度不匹配】 - {filename} - 第{week}周第{day}天 - {theme}\n    标题：{title}\n    内容过于复杂，不适合2年级学生：{text}")

                        # 检查annotation是否包含说明性句子（应该只有字词解释）
                        if 'annotation' in content_block and content_block['annotation']:
                            annotation = content_block['annotation']
                            # 检查是否包含说明性句子（不是字词解释格式）
                            if '这是' in annotation or '表达' in annotation or '说明' in annotation:
                                if not re.search(r'[：:].*[。！]', annotation):  # 如果不是字词解释格式
                                    report.append(f"【注解格式问题】 - {filename} - 第{week}周第{day}天 - {theme}\n    标题：{title}\n    注解应只包含字词解释，不应包含说明性句子：{annotation}")

            except json.JSONDecodeError as e:
                report.append(f"错误：文件 {filepath} JSON格式不正确: {e}")
            except Exception as e:
                report.append(f"错误：处理文件 {filepath} 时发生未知错误: {e}")
    return report

if __name__ == "__main__":
    base_directory = '/Users/trl_1/Downloads/0616/edu/晨读/morning_read_txt/内容'
    print("============================================================")
    print("2年级内容检查报告")
    print("============================================================")
    
    # 基础检查
    print("\n【基础检查】")
    basic_issues = check_grade_2_content(base_directory)
    
    # 逻辑检查
    print("\n【逻辑问题检查】")
    logic_issues = check_grade_2_logic_issues(base_directory)
    
    all_issues = basic_issues + logic_issues
    
    if all_issues:
        print(f"\n总计发现 {len(all_issues)} 个问题\n")
        
        # 分类报告
        missing_task = [i for i in all_issues if "【缺少task字段】" in i]
        missing_task_answer = [i for i in all_issues if "【缺少taskAnswer字段】" in i]
        pinyin_mismatch = [i for i in all_issues if "【拼音可能不匹配】" in i]
        typos = [i for i in all_issues if "【错别字/表达错误】" in i]
        content_patching = [i for i in all_issues if "【内容拼凑/不连贯】" in i]
        difficulty_issues = [i for i in all_issues if "【难度不匹配】" in i]
        annotation_issues = [i for i in all_issues if "【注解格式问题】" in i]
        
        if missing_task:
            print(f"\n【缺少task字段】共 {len(missing_task)} 处：")
            for issue in missing_task[:10]:  # 只显示前10个
                parts = issue.split(' - ')
                if len(parts) >= 4:
                    print(f"  - {parts[1]} - {parts[2]} - {parts[3]}\n    {parts[4] if len(parts) > 4 else ''}")
            if len(missing_task) > 10:
                print(f"  ... 还有 {len(missing_task) - 10} 处")

        if missing_task_answer:
            print(f"\n【缺少taskAnswer字段】共 {len(missing_task_answer)} 处：")
            for issue in missing_task_answer[:10]:
                parts = issue.split(' - ')
                if len(parts) >= 4:
                    print(f"  - {parts[1]} - {parts[2]} - {parts[3]}\n    {parts[4] if len(parts) > 4 else ''}")
            if len(missing_task_answer) > 10:
                print(f"  ... 还有 {len(missing_task_answer) - 10} 处")

        if pinyin_mismatch:
            print(f"\n【拼音可能不匹配】共 {len(pinyin_mismatch)} 处：")
            for issue in pinyin_mismatch[:10]:
                parts = issue.split('\n')
                print(f"  - {parts[0].split(' - ')[1]} - {parts[0].split(' - ')[2]} - {parts[0].split(' - ')[3]}")
                for part in parts[1:]:
                    print(f"    {part}")
            if len(pinyin_mismatch) > 10:
                print(f"  ... 还有 {len(pinyin_mismatch) - 10} 处")

        if typos:
            print(f"\n【错别字/表达错误】共 {len(typos)} 处：")
            for issue in typos:
                parts = issue.split('\n')
                print(f"  - {parts[0].split(' - ')[1]} - {parts[0].split(' - ')[2]} - {parts[0].split(' - ')[3]}")
                for part in parts[1:]:
                    print(f"    {part}")

        if content_patching:
            print(f"\n【内容拼凑/不连贯】共 {len(content_patching)} 处：")
            for issue in content_patching:
                parts = issue.split(' - ')
                if len(parts) >= 4:
                    print(f"  - {parts[1]} - {parts[2]} - {parts[3]}\n    {parts[4] if len(parts) > 4 else ''}")

        if difficulty_issues:
            print(f"\n【难度不匹配】共 {len(difficulty_issues)} 处：")
            for issue in difficulty_issues:
                parts = issue.split('\n')
                print(f"  - {parts[0].split(' - ')[1]} - {parts[0].split(' - ')[2]} - {parts[0].split(' - ')[3]}")
                for part in parts[1:]:
                    print(f"    {part}")

        if annotation_issues:
            print(f"\n【注解格式问题】共 {len(annotation_issues)} 处：")
            for issue in annotation_issues:
                parts = issue.split('\n')
                print(f"  - {parts[0].split(' - ')[1]} - {parts[0].split(' - ')[2]} - {parts[0].split(' - ')[3]}")
                for part in parts[1:]:
                    print(f"    {part}")
    else:
        print("未发现任何问题。")
    
    print("\n============================================================")
    print("检查完成")
    print("============================================================")
    
    # 保存详细报告到文件
    if all_issues:
        report_file = os.path.join(base_directory, '2年级内容检查报告.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 2年级内容检查报告\n\n")
            f.write("## 概述\n")
            f.write("本报告旨在检查2年级所有教学内容文件（JSON格式）的合理性，并识别需要调整优化的部分。\n\n")
            f.write("## 检查结果\n\n")
            f.write(f"总计发现 {len(all_issues)} 个问题。\n\n")
            
            # 写入详细问题
            if missing_task:
                f.write(f"### 【缺少task字段】 (共 {len(missing_task)} 处)\n\n")
                for issue in missing_task:
                    f.write(f"- {issue}\n\n")
            
            if missing_task_answer:
                f.write(f"### 【缺少taskAnswer字段】 (共 {len(missing_task_answer)} 处)\n\n")
                for issue in missing_task_answer:
                    f.write(f"- {issue}\n\n")
            
            if pinyin_mismatch:
                f.write(f"### 【拼音可能不匹配】 (共 {len(pinyin_mismatch)} 处)\n\n")
                for issue in pinyin_mismatch:
                    f.write(f"- {issue}\n\n")
            
            if typos:
                f.write(f"### 【错别字/表达错误】 (共 {len(typos)} 处)\n\n")
                for issue in typos:
                    f.write(f"- {issue}\n\n")
            
            if content_patching:
                f.write(f"### 【内容拼凑/不连贯】 (共 {len(content_patching)} 处)\n\n")
                for issue in content_patching:
                    f.write(f"- {issue}\n\n")
            
            if difficulty_issues:
                f.write(f"### 【难度不匹配】 (共 {len(difficulty_issues)} 处)\n\n")
                for issue in difficulty_issues:
                    f.write(f"- {issue}\n\n")
            
            if annotation_issues:
                f.write(f"### 【注解格式问题】 (共 {len(annotation_issues)} 处)\n\n")
                for issue in annotation_issues:
                    f.write(f"- {issue}\n\n")
            
            f.write("## 优化建议\n")
            f.write("1. **补充缺失的 `task` 和 `taskAnswer` 字段**：对于所有报告中指出的缺失任务和答案，应根据内容补充合适的学习任务和参考答案。\n")
            f.write("2. **修正拼音与汉字不匹配的问题**：仔细核对报告中列出的拼音与汉字不匹配的条目，修正拼音，使其与对应的汉字内容完全一致。\n")
            f.write("3. **修正错别字和不当表达**：根据报告中指出的具体问题，修正文本内容，确保语言的准确性和适宜性。\n")
            f.write("4. **简化或替换难度不匹配的内容**：对于对2年级学生过于复杂的内容，考虑简化表达，或替换为更符合其认知水平的简单句式和词语。\n")
            f.write("5. **扩充过短的绕口令**：对于内容过短的绕口令，考虑增加更多句子，以达到更好的练习效果。\n")
            f.write("6. **修正注解格式**：确保注解只包含字词解释，不包含说明性句子。\n")
        
        print(f"\n详细报告已保存到: {report_file}")

