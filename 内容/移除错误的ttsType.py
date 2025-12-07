#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移除被错误添加的ttsType（现代文不应该有ttsType）
只保留真正的古诗词、国学经典、文言文的ttsType
"""
import json
import re
from pathlib import Path

def is_ancient_poem(title, content_text):
    """判断是否为古诗词 - 严格判断"""
    # 明确的古诗词标题关键词
    # 先排除现代文标题（避免误判）
    modern_exclude = [
        '纸船和风筝', '在牛肚子里旅行', '纸船', '风筝',
        '拍手歌', '场景歌', '树之歌', '田家四季歌', '对韵歌', '韵母歌', '声母歌',
        '小嘴巴', '声母宝宝', '学认汉字', '小船', '高楼', '安静', '唱歌',
        '秋天（节选）', '四季（节选）', '日月明', '小书包', '升国旗',
        '小小的船', '比尾巴', '乌鸦喝水', '植物妈妈有办法',
        '丁香结', '花之歌', '月光曲', '草原'  # 现代文
    ]
    
    for exclude in modern_exclude:
        if exclude in title:
            return False
    
    poem_keywords = [
        '池上', '所见', '敕勒歌', '望洞庭', '静夜思', '春晓',
        '登鹳雀楼', '悯农', '咏鹅', '江南', '古朗月行',
        '绝句', '春夜喜雨', '江雪', '寻隐者不遇', '山行',
        '清明', '元日', '泊船瓜洲', '书湖阴先生壁', '六月二十七日望湖楼醉书',
        '西江月', '清平乐', '水调歌头', '满江红', '虞美人',
        '过零丁洋', '竹枝词', '浪淘沙', '忆江南', '渔歌子',
        '梅花', '望庐山瀑布', '枫桥夜泊', '山居秋暝', '宿建德江',
        '七律·长征', '己亥杂诗', '题临安邸', '雪梅'
    ]
    
    # 检查标题是否包含明确的古诗词名称（完整匹配，避免单字"风"误判）
    for keyword in poem_keywords:
        if keyword in title:
            return True
    
    # 检查是否是明确的诗词格式（排除现代儿歌和现代文）
    if re.search(r'^[^（]*[诗词歌行曲赋吟咏]（', title):
        # 排除现代儿歌和现代文
        exclude_keywords = ['拍手歌', '场景歌', '树之歌', '田家四季歌', '对韵歌', '韵母歌', '声母歌', 
                           '纸船和风筝', '在牛肚子里旅行', '纸船', '风筝']
        if not any(exclude in title for exclude in exclude_keywords):
            return True
    
    return False

def is_classics(title, content_text):
    """判断是否为国学经典"""
    classics_keywords = [
        '论语', '孟子', '大学', '中庸', '三字经', '弟子规',
        '千字文', '百家姓', '增广贤文', '幼学琼林', '声律启蒙',
        '道德经', '庄子', '列子', '韩非子', '淮南子', '菜根谭',
        '诗经', '尚书', '礼记', '周易', '春秋', '左传',
        '古人谈读书', '精卫填海', '王戎不取道旁李', '伯牙鼓琴', '书戴嵩画牛'
    ]
    
    for keyword in classics_keywords:
        if keyword in title:
            return True
    
    return False

def is_classical_chinese(content_text):
    """判断是否为文言文 - 严格判断"""
    if not content_text:
        return False
    
    # 移除括号内的注音
    content_clean = re.sub(r'（[^）]*）', '', content_text)
    content_clean = re.sub(r'\([^)]*\)', '', content_clean)
    
    # 文言文常见虚词
    classical_particles = ['之', '乎', '者', '也', '矣', '焉', '哉', '欤', '耶', '尔', '而', '以', '于', '为', '所', '其', '乃', '则', '若', '然', '故', '盖', '夫']
    
    # 统计文言虚词出现频率
    particle_count = sum(1 for particle in classical_particles if particle in content_clean)
    total_chars = len(re.findall(r'[\u4e00-\u9fff]', content_clean))
    
    # 如果文言虚词占比超过10%，且总字数超过30，可能是文言文
    if total_chars > 30 and particle_count / total_chars > 0.10:
        return True
    
    # 检查是否有明显的文言文句式（排除现代文中的常见表达）
    # 排除现代文中的叠词（如"乎乎"、"乎乎地"）
    if re.search(r'乎乎[地]?', content_clean):
        return False
    
    # 排除现代文中的"何以"（在现代文中也很常见）
    if '何以' in content_clean and '何以古人' not in content_clean:
        # 如果"何以"后面不是文言文结构，可能是现代文
        if not re.search(r'何以[之|其|为]', content_clean):
            return False
    
    classical_patterns = [
        r'[之乎者也]{3,}',  # 连续的文言虚词（至少3个，避免"乎乎"误判）
        r'[何|孰|安|焉][以|为|能|可][之|其|为]',  # 文言疑问句式（更严格）
        r'[若|如|倘][则|即|乃][之|其|为]',  # 文言假设句式（更严格）
        r'[故|盖|夫][而|则|以][之|其|为]',  # 文言发语词（更严格）
    ]
    
    for pattern in classical_patterns:
        if re.search(pattern, content_clean):
            return True
    
    return False

def remove_wrong_ttstype(data, file_path):
    """移除错误的ttsType"""
    removed_count = 0
    modified = False
    
    for week_data in data:
        week_num = week_data.get('week', 0)
        day_num = week_data.get('day', 0)
        theme = week_data.get('theme', '')
        
        for content_item in week_data.get('content', []):
            if content_item.get('type') == 'textbook_review':
                if 'ttsType' in content_item and content_item['ttsType'] == 'all':
                    title = content_item.get('title', '')
                    
                    # 收集所有文本内容
                    content_texts = []
                    for obj in content_item.get('contentObject', []):
                        if isinstance(obj, dict) and 'text' in obj:
                            content_texts.append(obj['text'])
                    
                    content_text = ''.join(content_texts)
                    
                    # 判断是否真的是古诗词、国学经典或文言文
                    is_poem = is_ancient_poem(title, content_text)
                    is_classic = is_classics(title, content_text)
                    is_classical = is_classical_chinese(content_text)
                    
                    # 如果不是这三种类型，移除ttsType
                    if not (is_poem or is_classic or is_classical):
                        del content_item['ttsType']
                        removed_count += 1
                        modified = True
                        
                        file_ref = f"{file_path.name} - 第{week_num}周第{day_num}天 - {theme}"
                        print(f"移除ttsType: {file_ref}")
                        print(f"  标题: {title}")
                        print()
    
    return removed_count, modified

def process_all_files():
    """处理所有文件"""
    base_dir = Path(__file__).parent
    
    total_removed = 0
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
                
                removed_count, modified = remove_wrong_ttstype(data, txt_file)
                
                if modified:
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent='\t')
                    files_modified.append(txt_file.name)
                    total_removed += removed_count
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
                
                removed_count, modified = remove_wrong_ttstype(data, txt_file)
                
                if modified:
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent='\t')
                    files_modified.append(txt_file.name)
                    total_removed += removed_count
                    print(f"已保存: {txt_file.name}\n")
            
            except Exception as e:
                print(f"处理文件 {txt_file.name} 时出错: {str(e)}\n")
    
    print("=" * 80)
    print("处理完成")
    print("=" * 80)
    print(f"总计移除 {total_removed} 处错误的ttsType")
    print(f"修改了 {len(files_modified)} 个文件:")
    for filename in files_modified:
        print(f"  - {filename}")

if __name__ == "__main__":
    print("开始移除错误的ttsType...")
    print("=" * 80)
    process_all_files()

