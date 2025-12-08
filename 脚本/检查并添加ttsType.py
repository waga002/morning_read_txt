#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有"type":"textbook_review"的文章，如果实际内容为古诗词、国学经典、文言文，
给文章增加"ttsType": "all"
"""
import json
import re
from pathlib import Path

def is_ancient_poem(title, content_text):
    """判断是否为古诗词"""
    # 明确的古诗词标题关键词
    poem_keywords = [
        '池上', '所见', '敕勒歌', '望洞庭', '静夜思', '春晓',
        '登鹳雀楼', '悯农', '咏鹅', '风', '江南', '古朗月行',
        '绝句', '春夜喜雨', '江雪', '寻隐者不遇', '山行',
        '清明', '元日', '泊船瓜洲', '书湖阴先生壁', '六月二十七日望湖楼醉书',
        '西江月', '清平乐', '水调歌头', '满江红', '虞美人',
        '过零丁洋', '竹枝词', '浪淘沙', '忆江南', '渔歌子',
        '梅花', '望庐山瀑布'
    ]
    
    # 检查标题是否包含明确的古诗词名称
    for keyword in poem_keywords:
        if keyword in title:
            return True
    
    # 检查标题格式（诗、词、歌、行等）
    if re.search(r'[诗词歌行曲赋吟咏]$', title) or re.search(r'^[^（]*[诗词歌行曲赋]', title):
        # 排除现代文（如"拍手歌"可能是现代儿歌）
        if '拍手歌' not in title and '场景歌' not in title and '树之歌' not in title:
            return True
    
    return False

def is_classics(title, content_text):
    """判断是否为国学经典"""
    # 常见国学经典关键词
    classics_keywords = [
        '论语', '孟子', '大学', '中庸', '三字经', '弟子规',
        '千字文', '百家姓', '增广贤文', '幼学琼林', '声律启蒙',
        '道德经', '庄子', '列子', '韩非子', '淮南子', '菜根谭',
        '诗经', '尚书', '礼记', '周易', '春秋', '左传'
    ]
    
    for keyword in classics_keywords:
        if keyword in title:
            return True
    
    return False

def is_classical_chinese(content_text):
    """判断是否为文言文"""
    if not content_text:
        return False
    
    # 文言文常见虚词
    classical_particles = ['之', '乎', '者', '也', '矣', '焉', '哉', '欤', '耶', '尔', '而', '以', '于', '为', '所', '其', '乃', '则', '若', '然', '故', '盖', '夫']
    
    # 统计文言虚词出现频率
    particle_count = sum(1 for particle in classical_particles if particle in content_text)
    total_chars = len(re.findall(r'[\u4e00-\u9fff]', content_text))
    
    # 如果文言虚词占比超过8%，且总字数超过20，可能是文言文
    if total_chars > 20 and particle_count / total_chars > 0.08:
        return True
    
    # 检查是否有明显的文言文句式（更严格）
    classical_patterns = [
        r'[之乎者也]{2,}',  # 连续的文言虚词（至少2个）
        r'[何|孰|安|焉][以|为|能|可]',  # 文言疑问句式
        r'[若|如|倘][则|即|乃]',  # 文言假设句式
        r'[故|盖|夫][而|则|以]',  # 文言发语词
    ]
    
    for pattern in classical_patterns:
        if re.search(pattern, content_text):
            return True
    
    return False

def check_and_add_ttstype(data, file_path):
    """检查并添加ttsType"""
    fixed_count = 0
    modified = False
    
    for week_data in data:
        week_num = week_data.get('week', 0)
        day_num = week_data.get('day', 0)
        theme = week_data.get('theme', '')
        
        for content_item in week_data.get('content', []):
            if content_item.get('type') == 'textbook_review':
                # 如果已经有ttsType，跳过
                if 'ttsType' in content_item:
                    continue
                
                title = content_item.get('title', '')
                
                # 收集所有文本内容
                content_texts = []
                for obj in content_item.get('contentObject', []):
                    if isinstance(obj, dict) and 'text' in obj:
                        content_texts.append(obj['text'])
                
                content_text = ''.join(content_texts)
                
                # 判断是否为古诗词、国学经典或文言文
                is_poem = is_ancient_poem(title, content_text)
                is_classic = is_classics(title, content_text)
                is_classical = is_classical_chinese(content_text)
                
                if is_poem or is_classic or is_classical:
                    content_item['ttsType'] = 'all'
                    fixed_count += 1
                    modified = True
                    
                    type_desc = []
                    if is_poem:
                        type_desc.append('古诗词')
                    if is_classic:
                        type_desc.append('国学经典')
                    if is_classical:
                        type_desc.append('文言文')
                    
                    file_ref = f"{file_path.name} - 第{week_num}周第{day_num}天 - {theme}"
                    print(f"添加ttsType: {file_ref}")
                    print(f"  标题: {title}")
                    print(f"  类型: {', '.join(type_desc)}")
                    print()
    
    return fixed_count, modified

def process_all_files():
    """处理所有文件"""
    base_dir = Path(__file__).parent
    
    total_fixed = 0
    files_modified = []
    
    # 检查有拼音的1年级和2年级文件
    for grade in [1, 2]:
        grade_dir = base_dir / "有拼音" / f"{grade}年级"
        if not grade_dir.exists():
            continue
        
        txt_files = sorted(grade_dir.glob("*.txt"))
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                fixed_count, modified = check_and_add_ttstype(data, txt_file)
                
                if modified:
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent='\t')
                    files_modified.append(txt_file.name)
                    total_fixed += fixed_count
                    print(f"已保存: {txt_file.name}\n")
            
            except Exception as e:
                print(f"处理文件 {txt_file.name} 时出错: {str(e)}\n")
    
    # 检查无拼音的3-6年级文件
    for grade in [3, 4, 5, 6]:
        grade_dir = base_dir / "无拼音" / f"{grade}年级"
        if not grade_dir.exists():
            continue
        
        txt_files = sorted(grade_dir.glob("*.txt"))
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                fixed_count, modified = check_and_add_ttstype(data, txt_file)
                
                if modified:
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent='\t')
                    files_modified.append(txt_file.name)
                    total_fixed += fixed_count
                    print(f"已保存: {txt_file.name}\n")
            
            except Exception as e:
                print(f"处理文件 {txt_file.name} 时出错: {str(e)}\n")
    
    print("=" * 80)
    print("处理完成")
    print("=" * 80)
    print(f"总计添加 {total_fixed} 处ttsType")
    print(f"修改了 {len(files_modified)} 个文件:")
    for filename in files_modified:
        print(f"  - {filename}")

if __name__ == "__main__":
    print("开始检查并添加ttsType...")
    print("=" * 80)
    process_all_files()

