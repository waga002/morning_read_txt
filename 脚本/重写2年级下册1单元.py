#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重写「二年级下册 第1单元」晨读内容（两周12天）。

目标风格（2年级）：
- 从“字词”过渡到“句/段”，句子更长但要顺
- 每天围绕课本单元主题（春天/发现/植树/口语语气/语文园地/快乐读书吧）
- 每天固定板块：课本复习 +（短文/故事/童诗/经典/古诗）+ 写话/积累
- 任务必须可操作，给出 taskAnswer 范例

输出到（不覆盖原文件）：
  内容/有拼音_重写版/下学期/2年级/2年级下册1单元.txt
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pypinyin import Style, lazy_pinyin


ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = ROOT / "内容" / "有拼音_重写版" / "下学期" / "2年级" / "2年级下册1单元.txt"


def _only_han(s: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fff]", s or ""))


def py(s: str) -> str:
    """仅对汉字生成拼音（带声调），忽略标点/数字/英文字母等。"""
    han = _only_han(s)
    if not han:
        return ""
    return " ".join(lazy_pinyin(han, style=Style.TONE))


def line(text: str) -> Dict[str, str]:
    return {"pinyin": py(text), "text": text}


def base_fields() -> Dict[str, str]:
    return {
        "author": "",
        "authorPinyin": "",
        "dynasty": "",
        "dynastyPinyin": "",
        "annotation": "",
        "annotationPinyin": "",
        "translation": "",
        "translationPinyin": "",
        "appreciation": "",
        "appreciationPinyin": "",
    }


def item(
    title: str,
    typ: str,
    content_lines: List[str],
    task: str,
    task_answer: str,
    *,
    author: str = "",
    dynasty: str = "",
    annotation: str = "",
    translation: str = "",
    appreciation: str = "",
    alignment_mode: str = "left",
    paragraph_indent: int = 2,
) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        "title": title,
        "titlePinyin": py(title),
        "type": typ,
        "contentObject": [line(t) for t in content_lines],
        "task": task,
        "taskPinyin": py(task),
        "taskAnswer": task_answer,
        "taskAnswerPinyin": py(task_answer),
        "alignment_mode": alignment_mode,
        "paragraph_indent": paragraph_indent,
        **base_fields(),
    }
    if author:
        d["author"] = author
        d["authorPinyin"] = py(author)
    if dynasty:
        d["dynasty"] = dynasty
        d["dynastyPinyin"] = py(dynasty)
    if annotation:
        d["annotation"] = annotation
        d["annotationPinyin"] = py(annotation)
    if translation:
        d["translation"] = translation
        d["translationPinyin"] = py(translation)
    if appreciation:
        d["appreciation"] = appreciation
        d["appreciationPinyin"] = py(appreciation)
    return d


def daily(
    title: str,
    rows: List[str],
    task: str,
    task_answer: str,
) -> Dict[str, Any]:
    def _task_for_title(t: str) -> str:
        t = (t or "").strip()
        t = re.sub(r"[。！？!?]+$", "", t)
        return t

    def _is_sentence_task(t: str) -> bool:
        t = t or ""
        # 这类晨读里“写句子/造句/扩句/润色/仿写/用某词说一句”等
        return any(
            k in t
            for k in [
                "说一句",
                "写一句",
                "造句",
                "扩写",
                "扩写成",
                "润色",
                "照样子",
                "仿写",
                "比喻句",
                "拟人的话",
                "扩写得更具体",
                "更生动",
                "更具体",
            ]
        )

    is_sentence = _is_sentence_task(task)

    # 默认：保留 task/taskAnswer 字段（用于系统/家长查看）
    # 若是“写句子类”内容：把要求放进 title 括号里，把范例放进 content 里，保证学生只读正文也能完成晨读。
    inner_title = title
    if is_sentence:
        inner_title = f"{title}（{_task_for_title(task)}）"

    return {
        "title": "日积月累",
        "titlePinyin": py("日积月累"),
        "type": "daily_accumulation",
        "contentObject": [
            {
                "title": inner_title,
                "titlePinyin": py(inner_title),
                "content": [line(r) for r in rows]
                + ([line(f"范例：{task_answer}")] if is_sentence and task_answer else []),
            }
        ],
        "task": "" if is_sentence else task,
        "taskPinyin": "" if is_sentence else py(task),
        "taskAnswer": "" if is_sentence else task_answer,
        "taskAnswerPinyin": "" if is_sentence else py(task_answer),
        **base_fields(),
    }


def week_day(week: int, day: int, theme: str, content: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"grade": 2, "term": 1, "week": week, "day": day, "theme": theme, "content": content}


def build() -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []

    # 固定模板（增强版，二年级晨读更聚焦）
    # 周一：课本复习 + 现代短文 + 古诗 + 好词(6)
    # 周二：课本复习 + 寓言/故事 +（国学经典/小古文二选一）+ 好句(2)
    # 周三（写话日）：现代短文（短）+ 写话技巧 + 仿说/扩句 + 好词
    # 周四：课本复习 + 现代短文 + 寓言/故事 + 仿写（偏口头）
    # 周五：课本复习 + 古诗 + 四字词语/成语 + 句子润色
    # 周六：儿童诗 + 儿童故事 + 谚语/歇后语(3) + 口语交际（语气/礼貌）

    # Week 1 Day 1（周一）
    data.append(
        week_day(
            1,
            1,
            "春天悄悄来了",
            [
                item(
                    "找春天（节选）",
                    "textbook_review",
                    ["春天像个害羞的小姑娘，遮遮掩掩，躲躲藏藏。", "我们仔细地找哇，找哇。", "小草从地下探出头来，那是春天的眉毛吧？"],
                    "用“遮遮掩掩”说一句话。",
                    "小猫躲在门后，遮遮掩掩地看着我。",
                    appreciation="这段话用比喻和叠词，把“找春天”写得生动又有趣。",
                ),
                item(
                    "春天的消息（小短文）",
                    "modern_prose",
                    ["风轻轻地吹，柳枝轻轻地摆。", "小河解开了冰，叮咚叮咚唱起来。", "我闻到泥土的清香，看到新芽在发亮。", "原来，春天已经来到身边。"],
                    "短文里写到了哪些“春天的消息”？说出两个。",
                    "柳枝轻轻摆，小河叮咚唱。",
                ),
                item(
                    "村居",
                    "ancient_poem",
                    ["草长莺飞二月天，", "拂堤杨柳醉春烟。", "儿童散学归来早，", "忙趁东风放纸鸢。"],
                    "把这首诗背给家人听。",
                    "草长莺飞二月天，拂堤杨柳醉春烟。儿童散学归来早，忙趁东风放纸鸢。",
                    author="高鼎",
                    dynasty="清",
                    annotation="拂(fú)堤：轻轻拂过河堤。纸鸢(yuān)：风筝。",
                    translation="二月里青草长起来，黄莺飞来飞去。柳条拂过河堤，像在春雾里沉醉。孩子们放学回来得早，赶着东风放风筝。",
                    appreciation="诗里有景、有动、有孩子的快乐，画面感很强。",
                ),
                daily(
                    "好词积累",
                    ["春风拂面", "万物复苏", "花红柳绿", "兴高采烈", "寻找", "发芽"],
                    "选两个词语，写（说）一句通顺的话。",
                    "春风拂面，我在公园里寻找发芽的小草。",
                ),
            ],
        )
    )

    # Week 1 Day 2（周二）
    data.append(
        week_day(
            1,
            2,
            "小路开满花",
            [
                item(
                    "开满鲜花的小路（节选）",
                    "textbook_review",
                    ["鼹鼠先生收到一个包裹。", "他打开一看，里面是许多小种子。", "春天到了，小路两旁开满了鲜花。"],
                    "“开满鲜花的小路”像什么？用“像……”说一句。",
                    "开满鲜花的小路像一条五彩的地毯。",
                    appreciation="把小路比作地毯，句子更形象。",
                ),
                item(
                    "狐狸和乌鸦（小寓言）",
                    "story_legend",
                    ["乌鸦叼着一块肉，站在树枝上。", "狐狸夸它唱歌好听，想骗它开口。", "乌鸦一开口，肉掉下去了。", "狐狸叼走肉，乌鸦后悔极了。"],
                    "这个故事提醒我们什么？",
                    "不要轻信别人的花言巧语。",
                ),
                item(
                    "论语一句",
                    "classics",
                    ["与朋友交，言而有信。"],
                    "把这句话换成自己的话说一说。",
                    "和朋友相处，说话要算数。",
                    annotation="信：守信用。",
                    translation="和朋友交往，要守信用。",
                ),
                daily(
                    "好句积累（2句）",
                    ["春风像一只看不见的手，把柳枝轻轻摇醒。（比喻）", "小草从泥土里钻出来，眨着亮晶晶的眼睛。（拟人）"],
                    "照样子写（说）一句：把“小花开了”写得更生动。",
                    "小花开了，笑眯眯地向我点头。（拟人）",
                ),
            ],
        )
    )

    # Week 1 Day 3（周三：写话日）
    data.append(
        week_day(
            1,
            3,
            "写话日：把句子写具体",
            [
                item(
                    "春天在校园（短文）",
                    "modern_prose",
                    ["操场边的迎春花开了，黄黄的一串串。", "下课铃一响，笑声像小鸟一样飞出来。", "我一边走一边看，春天就在我的身边。"],
                    "短文里写到了哪些春天的景物？说出两个。",
                    "迎春花和春风。",
                ),
                daily(
                    "写话技巧：因为……所以……",
                    ["例句：因为春天来了，所以小草冒出了嫩芽。", "例句：因为下过一场雨，所以空气特别清新。"],
                    "用“因为……所以……”写（说）一句话。",
                    "因为我坚持练字，所以我的字越来越工整。",
                ),
                daily(
                    "仿说/扩句",
                    ["题1：把“柳条摆动。”扩写得更具体。（加上颜色、动作、地点）", "题2：把“孩子们很开心。”扩写得更具体。（加上原因、表情）"],
                    "任选一题，说一句扩写后的句子。",
                    "嫩绿的柳条在河边轻轻摆动，像在跳舞。",
                ),
                daily(
                    "好词积累",
                    ["嫩绿", "清香", "明媚", "轻轻"],
                    "用“明媚”说一句话。",
                    "今天阳光明媚，我们去公园散步。",
                ),
            ],
        )
    )

    # Week 1 Day 4（周四）
    data.append(
        week_day(
            1,
            4,
            "一起去植树",
            [
                item(
                    "邓小平爷爷植树（节选）",
                    "textbook_review",
                    ["春风拂面，阳光明媚。", "邓小平爷爷来到天坛公园植树。", "他挖坑、扶苗、填土、浇水，动作很认真。"],
                    "把“挖坑、扶苗、填土、浇水”按顺序说一遍。",
                    "先挖坑，再扶苗，然后填土，最后浇水。",
                    appreciation="用一连串动作写清楚“植树”的过程。",
                ),
                item(
                    "小树的心愿（短文）",
                    "modern_prose",
                    ["小树说：“我想长高一点。”", "小朋友说：“我给你浇水。”", "小树说：“我想更挺一点。”", "小朋友说：“我不折你的枝，不踩你的根。”"],
                    "短文里小朋友做了哪两件事来爱护小树？",
                    "给小树浇水，不折树枝不踩树根。",
                ),
                item(
                    "小青蛙找家（小故事）",
                    "story_legend",
                    ["小青蛙迷路了，急得团团转。", "小花说：“别着急，先看看路标。”", "小青蛙慢慢走，终于找到了池塘。", "它说：“谢谢你，我学会不慌张。”"],
                    "小青蛙为什么能找到家？",
                    "因为它不着急，先看路标，再慢慢走。",
                ),
                daily(
                    "仿写（口头也可以）",
                    ["例句：他挖坑、扶苗、填土、浇水，动作很认真。"],
                    "照样子说一句：用四个动作写一写你做的一件事。",
                    "我洗手、摆碗筷、端饭菜、收桌子，动作很麻利。",
                ),
            ],
        )
    )

    # Week 1 Day 5（周五）
    data.append(
        week_day(
            1,
            5,
            "古诗里的春风",
            [
                item(
                    "古诗二首",
                    "textbook_review",
                    ["《村居》：草长莺飞二月天。", "《村居》：拂堤杨柳醉春烟。", "《咏柳》：碧玉妆成一树高。", "《咏柳》：二月春风似剪刀。"],
                    "先读《村居》两句，再读《咏柳》两句。读完选一句你最喜欢的，再读一遍。",
                    "我最喜欢《咏柳》：二月春风似剪刀。",
                ),
                item(
                    "咏柳",
                    "ancient_poem",
                    ["碧玉妆成一树高，", "万条垂下绿丝绦。", "不知细叶谁裁出，", "二月春风似剪刀。"],
                    "把这首诗背给同桌听。",
                    "碧玉妆成一树高，万条垂下绿丝绦。不知细叶谁裁出，二月春风似剪刀。",
                    author="贺知章",
                    dynasty="唐",
                    annotation="绦(tāo)：丝带。裁(cái)：剪裁。",
                    translation="高高的柳树像用碧玉打扮的一样，许多柳条垂下来像绿色的丝带。不知道细细的叶子是谁剪出来的，原来是二月春风像剪刀。",
                    appreciation="用比喻把景物写活，是学习写景的好范例。",
                ),
                daily(
                    "四字词语/成语",
                    ["花红柳绿（景色很美）", "春光明媚（阳光明亮）", "一丝不苟（非常认真）"],
                    "选一个词语，说一句话。",
                    "春光明媚，我们在操场上跑步。",
                ),
                daily(
                    "句子润色",
                    ["原句：小路很漂亮。", "提示：加上颜色、气味或像什么。"],
                    "把原句说得更生动。",
                    "小路开满了香香的花，像一条彩色的地毯。",
                ),
            ],
        )
    )

    # Week 1 Day 6（周六）
    data.append(
        week_day(
            1,
            6,
            "春天的儿童故事",
            [
                item(
                    "春天小童诗",
                    "children_poem",
                    ["一朵花开，", "就像点亮一盏灯。", "一阵风来，", "就把香味送远了。"],
                    "诗里把什么比作“灯”？",
                    "把“花开”比作点亮一盏灯。",
                ),
                item(
                    "小刺猬借雨伞（小故事）",
                    "story_legend",
                    ["下雨了，小刺猬要回家。", "他没有雨伞，就去找小兔子借。", "小兔子说：“当然可以，不过要轻轻拿。”", "小刺猬说：“谢谢你，我会爱护的！”"],
                    "小兔子提醒小刺猬什么？",
                    "要轻轻拿，爱护雨伞。",
                ),
                daily(
                    "谚语/歇后语",
                    ["春天的竹笋——节节高。（进步快）", "春雨贵如油。（春雨很宝贵）", "一口吃不成胖子。（要一步一步来）"],
                    "选一句，用自己的话解释。",
                    "“一口吃不成胖子”意思是：不能着急，要一步一步来。",
                ),
                item(
                    "口语交际：注意说话的语气",
                    "textbook_review",
                    ["同一句话，用不同语气，说出来的感觉不一样。", "请求时语气温柔一点，别人更愿意帮忙。"],
                    "把“给我看看你的书！”换成更有礼貌的一句话。",
                    "请把你的书借我看看，好吗？",
                ),
            ],
        )
    )

    # Week 2 Day 1（周一）
    data.append(
        week_day(
            2,
            1,
            "继续去找春天",
            [
                item(
                    "找春天（再读一段）",
                    "textbook_review",
                    ["我们看到了她，我们听到了她，我们闻到了她，我们触到了她。", "她在柳枝上荡秋千，在风筝尾巴上摇啊摇。"],
                    "用“……在……，在……”说一句话。",
                    "小鸟在树上唱歌，在天空中飞翔。",
                ),
                item(
                    "春天在校园（小短文）",
                    "modern_prose",
                    ["操场边的迎春花开了，黄黄的一串串。", "同学们跑步时，衣角被风吹得飘起来。", "下课铃一响，笑声像小鸟一样飞出来。", "校园里，到处都是春天。"],
                    "短文里写了哪两种春天的景物？",
                    "迎春花和春风。",
                ),
                item(
                    "村居（巩固）",
                    "ancient_poem",
                    ["草长莺飞二月天，", "拂堤杨柳醉春烟。", "儿童散学归来早，", "忙趁东风放纸鸢。"],
                    "读诗时，哪一句可以读得更快乐？说说看。",
                    "“忙趁东风放纸鸢”可以读得更快乐。",
                    author="高鼎",
                    dynasty="清",
                ),
                daily(
                    "好词积累",
                    ["嫩绿", "清香", "明媚", "温柔", "探出头", "摇来摇去"],
                    "用“探出头”写（说）一句话。",
                    "小草从土里探出头来，看看外面的世界。",
                ),
            ],
        )
    )

    # Week 2 Day 2（周二：小古文/国学二选一 → 这里放小古文）
    data.append(
        week_day(
            2,
            2,
            "故事里学表达",
            [
                item(
                    "开满鲜花的小路（再读一段）",
                    "textbook_review",
                    ["春风一吹，花儿都醒了。", "小路像穿上了彩色的衣服。", "大家看到鲜花，心里也开出了花。"],
                    "把“花开了”写成一句拟人的话。",
                    "花儿开了，笑眯眯地向我点头。",
                ),
                item(
                    "小熊借彩笔（小故事）",
                    "story_legend",
                    ["小熊想借彩笔。", "他一开始说：“给我彩笔！”", "小兔子皱了皱眉。", "小熊改口说：“请借我用一下，可以吗？”", "小兔子笑着把彩笔递给他。"],
                    "小熊后来为什么借到了彩笔？",
                    "因为他说话更有礼貌，语气更好。",
                ),
                item(
                    "小古文（极短）",
                    "classical_chinese",
                    ["春至，草木生。", "人勤，百事兴。"],
                    "把第一句换成白话说一说。",
                    "春天到了，草和树都长起来了。",
                    annotation="至：到。生：生长。勤：勤快。兴：兴旺。",
                    translation="春天到来，草木生长；人勤快，事情就更顺利。",
                ),
                daily(
                    "好句积累（2句）",
                    ["请借我用一下，可以吗？（礼貌请求）", "没关系，下次注意。（温柔回应）"],
                    "把“快点！”换成更温柔的一句话。",
                    "请你快一点，好吗？",
                ),
            ],
        )
    )

    # Week 2 Day 3（周三：写话日）
    data.append(
        week_day(
            2,
            3,
            "写话日：连词让句子更顺",
            [
                item(
                    "植树的一天（短文）",
                    "modern_prose",
                    ["今天我们去植树。", "我先挖坑，再扶苗，然后填土，最后浇水。", "看着小树站得笔直，我心里特别高兴。"],
                    "短文用了哪些顺序词？说出两个。",
                    "先、再（或：然后、最后）。",
                ),
                daily(
                    "写话技巧：先……再……然后……最后……",
                    ["例句：先洗手，再摆碗筷，然后坐好吃饭，最后把碗放回去。"],
                    "用这个顺序词写（说）一句“我做事”的话。",
                    "先整理书包，再穿好外套，然后跟老师说再见，最后回家。",
                ),
                daily(
                    "仿说/扩句",
                    ["题1：把“我很开心。”扩写得更具体。（加上原因和表情）", "题2：把“春风来了。”扩写得更具体。（加上动作和感觉）"],
                    "任选一题，说一句扩写后的句子。",
                    "我很开心，因为我种下了一棵小树，笑得合不拢嘴。",
                ),
                daily(
                    "好词积累",
                    ["认真", "笔直", "温柔", "清新"],
                    "用“清新”说一句话。",
                    "下过雨后，空气特别清新。",
                ),
            ],
        )
    )

    # Week 2 Day 4（周四）
    data.append(
        week_day(
            2,
            4,
            "比喻让画面更清楚",
            [
                item(
                    "邓小平爷爷植树（巩固）",
                    "textbook_review",
                    ["挖坑、扶苗、填土、浇水，一步一步做得很认真。", "小树苗像站好队的小朋友一样笔直。"],
                    "把“树苗很直”写成一句比喻句。",
                    "小树苗直直的，像小士兵一样站得笔挺。",
                ),
                item(
                    "小路像地毯（小短文）",
                    "modern_prose",
                    ["花开以后，小路变了样。", "红的、黄的、紫的花点点铺开。", "远远看去，小路像一条彩色地毯。", "走在上面，心里也像开了花。"],
                    "短文里把小路比作什么？",
                    "比作彩色地毯。",
                ),
                item(
                    "小猴子学说话（小故事）",
                    "story_legend",
                    ["小猴子说话很冲：“快点！”", "小鹿听了不开心。", "小猴子改口说：“请你快一点，好吗？”", "小鹿笑了，大家也更愿意帮忙。"],
                    "为什么改口后大家更愿意帮忙？",
                    "因为语气更礼貌温柔。",
                ),
                daily(
                    "仿写（口头也可以）",
                    ["例句：小路像一条彩色地毯。"],
                    "照样子说一句：用“像……”写一句比喻句。",
                    "迎春花像一串串小铃铛，挂在枝头。",
                ),
            ],
        )
    )

    # Week 2 Day 5（周五：语文园地落在周五更合适）
    data.append(
        week_day(
            2,
            5,
            "语文园地一：词句整理",
            [
                item(
                    "语文园地一（词句练习）",
                    "textbook_review",
                    ["把词语分分类，能帮助我们记得更牢。", "把句子写得具体，画面就更清楚。"],
                    "把“花”扩写成更具体的一句话。",
                    "公园里五颜六色的花开得正热闹。",
                ),
                item(
                    "咏柳（巩固）",
                    "ancient_poem",
                    ["碧玉妆成一树高，", "万条垂下绿丝绦。", "不知细叶谁裁出，", "二月春风似剪刀。"],
                    "从诗里选一句，读出画面感。",
                    "我选“万条垂下绿丝绦”。",
                    author="贺知章",
                    dynasty="唐",
                ),
                daily(
                    "四字词语/成语",
                    ["引人注目（特别显眼）", "兴高采烈（非常开心）", "万物复苏（万物苏醒）"],
                    "选一个词语，说一句话。",
                    "操场边的迎春花黄黄的，很引人注目。",
                ),
                daily(
                    "句子润色",
                    ["原句：春天很美。", "提示：加上颜色、气味或比喻。"],
                    "把原句说得更生动。",
                    "春天很美，花香甜甜的，像一幅彩色的画。",
                ),
            ],
        )
    )

    # Week 2 Day 6（周六：快乐读书吧）
    data.append(
        week_day(
            2,
            6,
            "快乐读书吧：读儿童故事",
            [
                item(
                    "春天小童诗",
                    "children_poem",
                    ["云朵像棉花糖，", "挂在蓝蓝的天上。", "笑声像小铃铛，", "叮当叮当响。"],
                    "找出诗里的两个比喻。",
                    "云朵像棉花糖；笑声像小铃铛。",
                ),
                item(
                    "会道歉的小狐狸（小故事）",
                    "story_legend",
                    ["小狐狸跑得太快，把小兔子的花盆撞倒了。", "小狐狸低下头说：“对不起，我不是故意的。”", "小兔子说：“没关系，我们一起把花种回去。”", "他们忙了一会儿，花又站起来了。"],
                    "小狐狸为什么被原谅了？",
                    "因为它真诚地道歉，还愿意一起补救。",
                ),
                item(
                    "快乐读书吧（读法小提示）",
                    "textbook_review",
                    ["读故事时，可以抓住“人物—事情—结果”。", "遇到好词好句，可以抄（记）在小本子上。"],
                    "用“人物—事情—结果”说一说刚才的故事。",
                    "小狐狸（人物）撞倒花盆并道歉（事情），小兔子原谅它并一起把花种回去（结果）。",
                ),
                daily(
                    "歇后语/俗语",
                    ["春天的竹笋——节节高。（进步快）", "滴水穿石——坚持就能成功。（坚持）", "一口吃不成胖子——做事要一步一步来。（循序渐进）"],
                    "选一句，用自己的话解释。",
                    "“一口吃不成胖子”意思是：不能着急，要一步一步来。",
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

