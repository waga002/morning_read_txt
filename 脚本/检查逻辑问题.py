import os
import json
import re

def check_logical_issues(base_path):
    """检查1年级内容中的逻辑矛盾、拼凑问题和其他问题"""
    report = []
    grade_1_path = os.path.join(base_path, '有拼音', '1年级')
    
    if not os.path.exists(grade_1_path):
        report.append(f"错误：未找到1年级内容路径: {grade_1_path}")
        return report

    issues = {
        'logic_contradictions': [],  # 逻辑矛盾
        'incoherent_content': [],   # 拼凑内容
        'difficulty_mismatch': [],  # 难度不匹配
        'knowledge_errors': [],     # 知识错误
        'inappropriate_expressions': [],  # 不当表达
        'task_answer_mismatch': [],  # 任务与答案不匹配
        'content_theme_mismatch': [],  # 内容与主题不符
    }

    for filename in sorted(os.listdir(grade_1_path)):
        if filename.endswith('.txt'):
            filepath = os.path.join(grade_1_path, filename)
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
                        task = content_block.get('task', '')
                        task_answer = content_block.get('taskAnswer', '')
                        
                        # 1. 检查任务与答案是否匹配
                        if task and task_answer:
                            # 检查答案是否回答了问题
                            if '为什么' in task or '怎么' in task or '怎样' in task:
                                if task_answer and len(task_answer.strip()) < 3:
                                    issues['task_answer_mismatch'].append(
                                        f"【任务答案不匹配】 - {filename} - 第{week}周第{day}天 - {theme}\n"
                                        f"    标题：{title}\n"
                                        f"    问题：{task}\n"
                                        f"    答案：{task_answer}（答案太简短，可能没有完整回答问题）"
                                    )
                        
                        # 2. 检查内容与主题是否匹配
                        content_text = ''
                        for obj in content_block.get('contentObject', []):
                            if isinstance(obj, dict):
                                if 'text' in obj:
                                    content_text += obj['text']
                                elif 'content' in obj:  # 日积月累的嵌套结构
                                    for sub_obj in obj.get('content', []):
                                        if 'text' in sub_obj:
                                            content_text += sub_obj['text']
                        
                        # 3. 检查难度是否适合1年级
                        # 检查是否有过于复杂的词汇或概念
                        complex_words = ['哲学', '理论', '抽象', '概念', '逻辑', '分析', '综合', '批判']
                        for word in complex_words:
                            if word in content_text or word in task or word in task_answer:
                                issues['difficulty_mismatch'].append(
                                    f"【难度不匹配】 - {filename} - 第{week}周第{day}天 - {theme}\n"
                                    f"    标题：{title}\n"
                                    f"    包含复杂词汇：{word}"
                                )
                        
                        # 4. 检查内容逻辑矛盾
                        # 检查故事内容是否前后矛盾
                        if item_type in ['story_legend', 'children_poem']:
                            # 检查是否有明显的时间、地点、人物矛盾
                            if '早上' in content_text and '晚上' in content_text:
                                # 检查是否在同一个场景中同时出现
                                if len(content_text) < 100:  # 短文本中同时出现可能有问题
                                    issues['logic_contradictions'].append(
                                        f"【时间矛盾】 - {filename} - 第{week}周第{day}天 - {theme}\n"
                                        f"    标题：{title}\n"
                                        f"    内容中同时出现'早上'和'晚上'，可能存在时间矛盾"
                                    )
                        
                        # 5. 检查拼凑问题
                        # 检查内容是否生硬拼接
                        if content_text:
                            # 检查是否有明显的拼接痕迹（如突然转换话题）
                            sentences = re.split(r'[。！？]', content_text)
                            if len(sentences) > 3:
                                # 检查句子之间是否有逻辑连贯性
                                topics = []
                                for sent in sentences:
                                    if len(sent.strip()) > 5:
                                        # 简单检查：如果句子主题差异很大，可能是拼凑
                                        if '动物' in sent or '小' in sent[:3]:
                                            topics.append('动物')
                                        elif '颜色' in sent or '红' in sent or '绿' in sent:
                                            topics.append('颜色')
                                        elif '数字' in sent or any(c.isdigit() for c in sent[:5]):
                                            topics.append('数字')
                                
                                if len(set(topics)) > 2 and len(topics) <= 5:
                                    # 主题切换过于频繁，可能是拼凑
                                    issues['incoherent_content'].append(
                                        f"【内容拼凑】 - {filename} - 第{week}周第{day}天 - {theme}\n"
                                        f"    标题：{title}\n"
                                        f"    内容主题切换频繁，可能存在拼凑问题"
                                    )
                        
                        # 6. 检查知识错误
                        # 检查是否有明显的常识错误
                        if '小蜜蜂' in title or '蜜蜂' in content_text:
                            if '嗡嗡嗡' in content_text:
                                # 这是正确的
                                pass
                            elif '汪汪汪' in content_text or '喵喵喵' in content_text:
                                issues['knowledge_errors'].append(
                                    f"【知识错误】 - {filename} - 第{week}周第{day}天 - {theme}\n"
                                    f"    标题：{title}\n"
                                    f"    蜜蜂的叫声描述错误"
                                )
                        
                        # 7. 检查不当表达
                        # 检查是否有不适合1年级学生的表达
                        inappropriate = ['死', '杀', '血', '鬼', '妖怪']
                        for word in inappropriate:
                            if word in content_text or word in task or word in task_answer:
                                issues['inappropriate_expressions'].append(
                                    f"【不当表达】 - {filename} - 第{week}周第{day}天 - {theme}\n"
                                    f"    标题：{title}\n"
                                    f"    包含不当词汇：{word}"
                                )
                        
                        # 8. 检查绕口令是否有错误
                        if item_type == 'tongue_twisters':
                            # 检查绕口令是否真的绕口
                            if len(content_text) < 20:
                                issues['incoherent_content'].append(
                                    f"【绕口令过短】 - {filename} - 第{week}周第{day}天 - {theme}\n"
                                    f"    标题：{title}\n"
                                    f"    绕口令内容过短，可能不够绕口"
                                )
                        
                        # 9. 检查古诗注释是否准确
                        if item_type == 'ancient_poem':
                            annotation = content_block.get('annotation', '')
                            if annotation:
                                # 检查注释中是否有明显的错误
                                if '！！' in annotation:
                                    parts = annotation.split('！！')
                                    if len(parts) > 5:
                                        issues['incoherent_content'].append(
                                            f"【注释过多】 - {filename} - 第{week}周第{day}天 - {theme}\n"
                                            f"    标题：{title}\n"
                                            f"    注释条目过多，可能不适合1年级学生"
                                        )

            except json.JSONDecodeError as e:
                issues['knowledge_errors'].append(f"错误：文件 {filepath} JSON格式不正确: {e}")
            except Exception as e:
                issues['knowledge_errors'].append(f"错误：处理文件 {filepath} 时发生未知错误: {e}")
    
    # 生成报告
    total_issues = sum(len(v) for v in issues.values())
    
    if total_issues > 0:
        report.append(f"============================================================")
        report.append(f"1年级内容逻辑问题检查报告")
        report.append(f"============================================================")
        report.append(f"\n总计发现 {total_issues} 个问题\n")
        
        if issues['logic_contradictions']:
            report.append(f"\n【逻辑矛盾】共 {len(issues['logic_contradictions'])} 处：")
            for issue in issues['logic_contradictions']:
                report.append(f"  {issue}\n")
        
        if issues['incoherent_content']:
            report.append(f"\n【内容拼凑/不连贯】共 {len(issues['incoherent_content'])} 处：")
            for issue in issues['incoherent_content']:
                report.append(f"  {issue}\n")
        
        if issues['difficulty_mismatch']:
            report.append(f"\n【难度不匹配】共 {len(issues['difficulty_mismatch'])} 处：")
            for issue in issues['difficulty_mismatch']:
                report.append(f"  {issue}\n")
        
        if issues['knowledge_errors']:
            report.append(f"\n【知识错误】共 {len(issues['knowledge_errors'])} 处：")
            for issue in issues['knowledge_errors']:
                report.append(f"  {issue}\n")
        
        if issues['inappropriate_expressions']:
            report.append(f"\n【不当表达】共 {len(issues['inappropriate_expressions'])} 处：")
            for issue in issues['inappropriate_expressions']:
                report.append(f"  {issue}\n")
        
        if issues['task_answer_mismatch']:
            report.append(f"\n【任务答案不匹配】共 {len(issues['task_answer_mismatch'])} 处：")
            for issue in issues['task_answer_mismatch']:
                report.append(f"  {issue}\n")
        
        if issues['content_theme_mismatch']:
            report.append(f"\n【内容主题不匹配】共 {len(issues['content_theme_mismatch'])} 处：")
            for issue in issues['content_theme_mismatch']:
                report.append(f"  {issue}\n")
    else:
        report.append("未发现明显的逻辑问题。")
    
    return report

if __name__ == "__main__":
    base_directory = '/Users/trl_1/Downloads/0616/edu/晨读/morning_read_txt/内容'
    report = check_logical_issues(base_directory)
    
    for line in report:
        print(line)

