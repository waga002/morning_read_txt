#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本功能：修复task和taskAnswer字段
当task字段包含多个问题时，taskAnswer中的回答应该用"！！"分隔
"""

import json
import os
import glob
import re

def count_questions(text):
    """统计文本中的问题数量（通过？和？）"""
    if not isinstance(text, str):
        return 0
    return text.count('？') + text.count('?')

def split_answer_by_keywords(answer, question_count):
    """
    尝试根据关键词智能分割回答
    常见模式：
    - "因为"、"由于" - 通常开始回答"为什么"
    - "如果"、"要是" - 通常开始回答假设性问题
    - "这"、"那" - 可能开始新的回答
    """
    if question_count <= 1:
        return answer
    
    # 如果已经有分隔符，直接返回
    if '！！' in answer:
        return answer
    
    # 尝试找到分割点
    # 模式1: 第一个问题通常是简短回答，第二个问题用"因为"、"如果"等开始
    patterns = [
        r'([^。！？]+[。！？])\s*(因为|由于|如果|要是|这|那|而|但|然而)',
        r'([^。！？]+[。！？])\s*([A-Za-z]|我|他|她|它|我们|他们)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, answer)
        if match:
            pos = match.end(1)
            # 在第一个回答后插入分隔符
            return answer[:pos] + '！！' + answer[pos:].lstrip()
    
    # 如果找不到明显的分割点，尝试在第一个句号后分割（如果回答足够长）
    if len(answer) > 50:
        # 找到第一个句号、感叹号或问号
        first_punct = re.search(r'[。！？]', answer)
        if first_punct:
            pos = first_punct.end()
            # 检查后面的内容是否足够长（至少20个字符）
            if len(answer[pos:]) > 20:
                return answer[:pos] + '！！' + answer[pos:].lstrip()
    
    return answer

def process_json_file(file_path):
    """
    处理单个JSON文件，修复task和taskAnswer字段
    """
    print(f"正在处理文件: {file_path}")
    
    # 读取文件
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  JSON解析错误: {e}")
        print(f"  跳过此文件\n")
        return 0
    
    # 统计修改数量
    modified_count = [0]
    
    # 递归处理JSON数据结构
    def process_item(item):
        if isinstance(item, dict):
            if 'task' in item and 'taskAnswer' in item:
                task = item['task']
                taskAnswer = item['taskAnswer']
                
                if isinstance(task, str) and isinstance(taskAnswer, str):
                    question_count = count_questions(task)
                    
                    # 如果有多个问题，检查taskAnswer是否有分隔符
                    if question_count > 1:
                        separator_count = taskAnswer.count('！！')
                        
                        # 如果分隔符数量不对
                        if separator_count != question_count - 1:
                            # 尝试智能分割
                            new_answer = split_answer_by_keywords(taskAnswer, question_count)
                            
                            if new_answer != taskAnswer:
                                item['taskAnswer'] = new_answer
                                modified_count[0] += 1
            
            # 递归处理所有值
            for key, value in item.items():
                process_item(value)
        elif isinstance(item, list):
            # 递归处理列表中的每个元素
            for element in item:
                process_item(element)
    
    # 处理数据
    process_item(data)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent='\t')
    
    print(f"完成！共修改了 {modified_count[0]} 个taskAnswer字段。\n")
    return modified_count[0]

def main():
    # 获取脚本所在目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 查找所有年级目录下的txt文件
    grade_dirs = ['3年级', '4年级', '5年级', '6年级']
    
    total_modified = 0
    total_files = 0
    
    for grade_dir in grade_dirs:
        grade_path = os.path.join(base_dir, grade_dir)
        if os.path.exists(grade_path):
            # 查找该目录下所有的txt文件
            txt_files = glob.glob(os.path.join(grade_path, '*.txt'))
            for file_path in sorted(txt_files):
                total_files += 1
                total_modified += process_json_file(file_path)
    
    print(f"所有文件处理完成！")
    print(f"共处理 {total_files} 个文件，总共修改了 {total_modified} 个taskAnswer字段。")
    print(f"\n注意：自动分割可能不够准确，请检查修改后的内容。")

if __name__ == "__main__":
    main()
