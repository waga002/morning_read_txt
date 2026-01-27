#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重写「1年级下册1单元」晨读内容（更口语、更顺、更适合一年级）。

输出到新目录（不覆盖原文件）：
  内容/有拼音_一年级重写版/下学期/1年级/1年级下册1单元.txt

运行：
  python3 脚本/重写1年级下册1单元.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from pypinyin import Style, lazy_pinyin


ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = (
    ROOT
    / "内容"
    / "有拼音_一年级重写版"
    / "下学期"
    / "1年级"
    / "1年级下册1单元.txt"
)


def extract_chinese(text: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fff]", text or ""))


def py(text: str) -> str:
    """只对汉字生成拼音（带声调），忽略标点/空格/数字等。"""
    s = extract_chinese(text)
    if not s:
        return ""
    return " ".join(lazy_pinyin(s, style=Style.TONE))


def line(text: str) -> Dict[str, str]:
    return {"pinyin": py(text), "text": text}


def item(
    title: str,
    typ: str,
    lines: List[str],
    task: str,
    task_answer: str = "",
    *,
    alignment_mode: str = "left",
    paragraph_indent: int = 2,
) -> Dict[str, Any]:
    return {
        "title": title,
        "titlePinyin": py(title),
        "type": typ,
        "contentObject": [line(t) for t in lines],
        "task": task,
        "taskPinyin": py(task),
        "taskAnswer": task_answer,
        "taskAnswerPinyin": py(task_answer),
        "alignment_mode": alignment_mode,
        "paragraph_indent": paragraph_indent,
    }


def daily_words(title: str, rows: List[str], task: str, task_answer: str = "") -> Dict[str, Any]:
    return {
        "title": "日积月累",
        "titlePinyin": py("日积月累"),
        "type": "daily_accumulation",
        "contentObject": [
            {
                "title": title,
                "titlePinyin": py(title),
                "content": [line(t) for t in rows],
            }
        ],
        "task": task,
        "taskPinyin": py(task),
        "taskAnswer": task_answer,
        "taskAnswerPinyin": py(task_answer),
    }


def day_block(week: int, day: int, theme: str, content: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"grade": 1, "term": 1, "week": week, "day": day, "theme": theme, "content": content}


def build() -> List[Dict[str, Any]]:
    # 设计原则（一年级晨读）：
    # - 每句尽量 6~12 字，口语化，朗读顺
    # - 少抽象说教，多具体场景
    # - 任务以“读/指/拍手/说一句” 为主，不要求写

    data: List[Dict[str, Any]] = []

    # 第1周
    data.append(
        day_block(
            1,
            1,
            "四季在身边",
            [
                item(
                    "四季歌",
                    "children_poem",
                    ["春天花开，真好看。", "夏天雨落，听叮当。", "秋天叶黄，像小船。", "冬天雪白，亮闪闪。"],
                    "拍一拍手，跟着读两遍。",
                    "",
                ),
                item(
                    "我的四季衣服",
                    "story_legend",
                    ["春天来了，我穿薄外套。", "太阳暖，我跑一跑。", "夏天热了，我戴小帽。", "秋天风大，我系围巾。", "冬天很冷，我穿棉衣。"],
                    "你最喜欢哪个季节？说一句“我喜欢……，因为……”。",
                    "我喜欢春天，因为花开了。",
                ),
                daily_words(
                    "词语小宝库",
                    ["春天", "夏天", "秋天", "冬天", "花开", "下雨"],
                    "挑两个词语，说一句话。",
                    "春天花开了。",
                ),
            ],
        )
    )

    data.append(
        day_block(
            1,
            2,
            "礼貌小朋友",
            [
                item(
                    "礼貌歌",
                    "children_poem",
                    ["见到老师说：您好！", "得到帮助说：谢谢！", "不小心碰到说：对不起！", "别人原谅说：没关系！"],
                    "指着四句话，大声读两遍。",
                ),
                item(
                    "小明会说谢谢",
                    "story_legend",
                    ["小明的铅笔掉了。", "小芳帮他捡起来。", "小明说：“谢谢你！”", "小芳笑着说：“不客气！”"],
                    "小明应该对小芳说什么？",
                    "谢谢你！",
                ),
                daily_words(
                    "会说的四句话",
                    ["请 -- 请你帮帮我", "谢谢 -- 谢谢老师", "对不起 -- 对不起，我错了", "没关系 -- 没关系"],
                    "你选一句，换成自己的话说一说。",
                    "请你帮帮我。",
                ),
            ],
        )
    )

    data.append(
        day_block(
            1,
            3,
            "上学路上",
            [
                item(
                    "早早上学",
                    "children_poem",
                    ["太阳出来笑哈哈。", "背上书包去学校。", "走路不跑不打闹。", "见到同学说声早。"],
                    "读两遍，最后一句说得更响亮。",
                ),
                item(
                    "排队不挤",
                    "story_legend",
                    ["下课了，大家去喝水。", "小朋友排好队。", "你让我，我让你。", "很快就轮到了我。"],
                    "排队时，我们要怎么做？",
                    "排好队，不推不挤。",
                ),
                daily_words(
                    "学说一句话：我在……做……",
                    ["我在教室读书。", "我在操场跑步。", "我在食堂吃饭。"],
                    "用这个句式，说一句你在学校做的事。",
                    "我在操场跳绳。",
                ),
            ],
        )
    )

    data.append(
        day_block(
            1,
            4,
            "小手真能干",
            [
                item(
                    "小手小手",
                    "children_poem",
                    ["小手洗干净，香喷喷。", "小手握铅笔，写认真。", "小手会整理，放整齐。", "小手拍拍手，真开心。"],
                    "边拍手边读两遍。",
                ),
                item(
                    "整理书包",
                    "story_legend",
                    ["放学回家，我打开书包。", "语文书放左边。", "数学书放右边。", "铅笔放进笔袋里。", "我的书包整整齐齐。"],
                    "你回家会整理什么？说一句。",
                    "我回家会整理书包。",
                ),
                daily_words(
                    "动作词",
                    ["洗手", "握笔", "整理", "收好", "摆正"],
                    "选一个动作词，说一句话。",
                    "我会洗手。",
                ),
            ],
        )
    )

    data.append(
        day_block(
            1,
            5,
            "春雨来了",
            [
                item(
                    "春雨滴答",
                    "children_poem",
                    ["滴答滴答，下雨啦。", "小花喝水笑哈哈。", "小草洗脸绿油油。", "我撑小伞回到家。"],
                    "学学雨声“滴答滴答”，再读两遍。",
                ),
                item(
                    "小伞不迷路",
                    "story_legend",
                    ["下雨了，路上有水坑。", "我慢慢走，不乱跑。", "我打着小伞，看着路。", "我安全回到家。"],
                    "下雨天走路要注意什么？",
                    "慢慢走，看着路。",
                ),
                daily_words(
                    "颜色词",
                    ["绿绿的", "红红的", "白白的", "蓝蓝的"],
                    "用“绿绿的”说一句话。",
                    "绿绿的小草在摇摆。",
                ),
            ],
        )
    )

    data.append(
        day_block(
            1,
            6,
            "爱护眼睛",
            [
                item(
                    "眼睛亮亮",
                    "children_poem",
                    ["眼睛亮亮看世界。", "看书坐直不趴着。", "写字别太靠近纸。", "远远看看小树叶。"],
                    "读两遍，做一做“坐直”的动作。",
                ),
                item(
                    "小明爱眼睛",
                    "story_legend",
                    ["小明看书坐得端端正正。", "灯光亮，他不眯眼。", "看一会儿，他抬头看看远处。", "妈妈说：“真棒！”"],
                    "小明做对了哪一件事？",
                    "他看一会儿就抬头看远处。",
                ),
                daily_words(
                    "好习惯",
                    ["坐直", "看远", "灯光亮", "不揉眼"],
                    "选一个词语，说一句话。",
                    "我看书会坐直。",
                ),
            ],
        )
    )

    # 第2周
    data.append(
        day_block(
            2,
            1,
            "左和右",
            [
                item(
                    "左手右手",
                    "children_poem",
                    ["左手拍拍，右手拍拍。", "左脚跺跺，右脚跺跺。", "我会分清左和右。", "走路更安全。"],
                    "跟着读两遍，做一做动作。",
                ),
                item(
                    "找一找左边",
                    "story_legend",
                    ["教室里有一扇窗。", "窗在黑板的左边。", "门在黑板的右边。", "我一下就找到了。"],
                    "门在黑板的哪一边？",
                    "右边。",
                ),
                daily_words(
                    "方位词",
                    ["左边", "右边", "上面", "下面", "前面", "后面"],
                    "用“在……上面/下面”说一句话。",
                    "书在桌子上面。",
                ),
            ],
        )
    )

    data.append(
        day_block(
            2,
            2,
            "动物朋友",
            [
                item(
                    "小动物真可爱",
                    "children_poem",
                    ["小猫喵喵，会捉鼠。", "小狗汪汪，看家门。", "小鸟啾啾，树上唱。", "小鱼游游，水里忙。"],
                    "读两遍，学学小动物的叫声。",
                ),
                item(
                    "小狗找球",
                    "story_legend",
                    ["小狗的球滚远了。", "它跑来跑去找。", "它闻一闻，听一听。", "它找到了球，开心极了。"],
                    "小狗是怎么找到球的？",
                    "它跑来跑去找到了球。",
                ),
                daily_words(
                    "学说一句话：谁在干什么",
                    ["小猫在睡觉。", "小狗在跑步。", "小鸟在唱歌。"],
                    "用这个句式，说一句你看到的画面。",
                    "小鱼在游泳。",
                ),
            ],
        )
    )

    data.append(
        day_block(
            2,
            3,
            "颜色在身边",
            [
                item(
                    "彩色世界",
                    "children_poem",
                    ["红红的花，开笑脸。", "绿绿的叶，轻轻摇。", "蓝蓝的天，白白的云。", "我爱彩色大自然。"],
                    "读两遍，找出儿歌里的颜色词。",
                    "红红的、绿绿的、蓝蓝的、白白的。",
                ),
                item(
                    "彩笔画画",
                    "story_legend",
                    ["我拿出彩笔。", "画红红的太阳。", "画绿绿的小树。", "画蓝蓝的天空。", "我说：“真漂亮！”"],
                    "你想画什么颜色的东西？",
                    "我想画黄黄的小鸭子。",
                ),
                daily_words(
                    "颜色词",
                    ["红红的", "绿绿的", "蓝蓝的", "黄黄的", "白白的"],
                    "用“红红的”说一句话。",
                    "红红的苹果真甜。",
                ),
            ],
        )
    )

    data.append(
        day_block(
            2,
            4,
            "安全小卫士",
            [
                item(
                    "安全儿歌",
                    "children_poem",
                    ["过马路，要慢走。", "先看左，再看右。", "不追跑，不打闹。", "安全回家笑一笑。"],
                    "读两遍，指一指“左”和“右”。",
                ),
                item(
                    "红灯停",
                    "story_legend",
                    ["路口亮起红灯。", "我停下来等一等。", "绿灯亮了，我再走。", "妈妈夸我真懂事。"],
                    "红灯亮时，我们要怎么做？",
                    "停下来等一等。",
                ),
                daily_words(
                    "安全小提醒",
                    ["不追跑", "不推挤", "走斑马线", "牵好大人"],
                    "选一条提醒，大声说给家人听。",
                    "过马路要走斑马线。",
                ),
            ],
        )
    )

    data.append(
        day_block(
            2,
            5,
            "好朋友手拉手",
            [
                item(
                    "好朋友",
                    "children_poem",
                    ["你帮我，我帮你。", "一起玩，不生气。", "有话好好说。", "我们是好朋友。"],
                    "读两遍，把“好朋友”说得更亲切。",
                ),
                item(
                    "借橡皮",
                    "story_legend",
                    ["我忘带橡皮了。", "我小声说：“请借我用一下。”", "同桌把橡皮递给我。", "我说：“谢谢！”"],
                    "我应该先说什么？",
                    "请借我用一下。",
                ),
                daily_words(
                    "会用的句子",
                    ["请你帮帮我。", "谢谢你。", "对不起。", "没关系。"],
                    "选一句，说给同桌/家人听。",
                    "谢谢你。",
                ),
            ],
        )
    )

    data.append(
        day_block(
            2,
            6,
            "快乐读书",
            [
                item(
                    "我爱读书",
                    "children_poem",
                    ["翻开书，看图画。", "小故事，真有趣。", "读一读，想一想。", "书里住着好朋友。"],
                    "读两遍，最后一句读得更慢更清楚。",
                ),
                item(
                    "小兔子看书",
                    "story_legend",
                    ["小兔子坐在桌前看书。", "它一页一页轻轻翻。", "看到好笑的地方，它笑了。", "看完书，它把书放回书架。"],
                    "看完书，我们应该把书放在哪里？",
                    "放回书架。",
                ),
                daily_words(
                    "学说一句话：我喜欢……",
                    ["我喜欢小猫。", "我喜欢画画。", "我喜欢读书。"],
                    "用这个句式，说一句你喜欢的事。",
                    "我喜欢踢球。",
                ),
            ],
        )
    )

    return data


def main() -> None:
    data = build()
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent="\t"), encoding="utf-8")
    print(f"已生成：{OUT_FILE}")


if __name__ == "__main__":
    main()

