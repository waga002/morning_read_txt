#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成「3年级下学期」1~8 单元晨读内容（无拼音_重写版），格式对齐你给的 Gemini 版本：

- 顶层：[{grade,term,week,day,theme,content:[...]}]
- 普通条目字段：title,type,author?,dynasty?,contentObject:[{text},...],annotation?,translation?,task,best_answer
- 古诗/小古文可含 dynasty/translation
- 日积月累：title=日积月累,type=daily_accumulation,contentObject=[{title,content:[{text},...]}],task,taskAnswer

输出目录：
  内容/无拼音_重写版/下学期/3年级/3年级下册{1..8}单元.txt

注意：
- 尽量原创/公版素材，避免复刻教材原文（课本复习用“画面概述/关键词”方式）
- “背诵/背一背/读X遍/拍手读/跟读/做动作”等不可书面表达任务：答案置空
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "内容" / "无拼音_重写版" / "下学期" / "3年级"


GENRE_PARENS = {"短文", "小短文", "小故事", "小寓言", "极短"}


def strip_genre_parens(title: str) -> str:
    """仅移除体裁标注括号（短文/小故事等）；保留节选/巩固等。"""
    if not title:
        return title

    def _repl(m: re.Match[str]) -> str:
        inner = (m.group(1) or "").strip()
        return "" if inner in GENRE_PARENS else m.group(0)

    return re.sub(r"（([^（）]+)）", _repl, title).strip()


def is_non_written_task(task: str) -> bool:
    t = (task or "").strip()
    if not t:
        return False
    if any(k in t for k in ["背诵", "背一背", "背背", "背会", "背给"]):
        return True
    if t.startswith("背") and not any(k in t for k in ["解释", "说说", "想一想", "为什么", "怎么", "写出", "找出"]):
        return True
    if any(k in t for k in ["拍手读", "跟读", "齐读", "大声读", "小声读"]):
        return True
    if re.search(r"读[一二三四五六七八九十0-9]+遍", t):
        if any(k in t for k in ["找出", "写出", "说说", "想一想", "解释", "为什么", "怎么", "哪", "什么", "多少", "几"]):
            return False
        return True
    if ("动作" in t and ("模仿" in t or "做" in t)) or "做一做" in t:
        if any(k in t for k in ["说说", "想一想", "解释", "为什么", "怎么"]):
            return False
        return True
    return False


def line(text: str) -> Dict[str, str]:
    return {"text": text}


def item(
    title: str,
    typ: str,
    lines: List[str],
    task: str,
    best_answer: str,
    *,
    author: str = "",
    dynasty: str = "",
    annotation: str = "",
    translation: str = "",
) -> Dict[str, Any]:
    title = strip_genre_parens(title)
    d: Dict[str, Any] = {
        "title": title,
        "type": typ,
        "contentObject": [line(t) for t in lines],
        "task": task,
        "best_answer": "" if is_non_written_task(task) else best_answer,
    }
    if author:
        d["author"] = author
    if dynasty:
        d["dynasty"] = dynasty
    if annotation:
        d["annotation"] = annotation
    if translation:
        d["translation"] = translation
    return d


def daily_accumulation(
    sections: List[Tuple[str, List[str]]],
    task: str,
    task_answer: str,
) -> Dict[str, Any]:
    return {
        "title": "日积月累",
        "type": "daily_accumulation",
        "contentObject": [{"title": t, "content": [line(x) for x in rows]} for t, rows in sections],
        "task": task,
        "taskAnswer": "" if is_non_written_task(task) else task_answer,
    }


def day_block(week: int, day: int, theme: str, content: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"grade": 3, "term": 1, "week": week, "day": day, "theme": theme, "content": content}


# 公版古诗（只放必要几首；避免重复）
POEMS: Dict[str, Dict[str, Any]] = {
    "绝句·迟日江山丽": {
        "author": "杜甫",
        "dynasty": "唐",
        "lines": ["迟日江山丽，", "春风花草香。", "泥融飞燕子，", "沙暖睡鸳鸯。"],
        "annotation": "迟日：春日。！！泥融：泥土湿润松软。！！鸳鸯：水鸟。",
        "translation": "春日阳光暖洋洋，江山格外明丽；春风带来花草的清香。泥土变得松软，燕子忙着飞来飞去；沙滩暖和，鸳鸯安静地睡着。",
    },
    "惠崇春江晚景": {
        "author": "苏轼",
        "dynasty": "宋",
        "lines": ["竹外桃花三两枝，", "春江水暖鸭先知。", "蒌蒿满地芦芽短，", "正是河豚欲上时。"],
        "annotation": "蒌蒿（lóu hāo）：一种野草。！！芦芽：芦苇嫩芽。",
        "translation": "竹林外几枝桃花开了，春水变暖，鸭子最先知道。地上长满蒌蒿，芦苇嫩芽才冒头，正是河豚想要逆流而上的时候。",
    },
    "三衢道中": {
        "author": "曾几",
        "dynasty": "宋",
        "lines": ["梅子黄时日日晴，", "小溪泛尽却山行。", "绿阴不减来时路，", "添得黄鹂四五声。"],
        "annotation": "三衢（qú）：地名。！！绿阴：树荫。！！黄鹂：鸟名。",
        "translation": "梅子黄的时候天天晴朗。我坐船走完小溪，又继续翻山赶路。树荫和来时一样浓密，还多听到黄鹂清脆的四五声。",
    },
    "元日": {
        "author": "王安石",
        "dynasty": "宋",
        "lines": ["爆竹声中一岁除，", "春风送暖入屠苏。", "千门万户曈曈日，", "总把新桃换旧符。"],
        "annotation": "屠苏：一种药酒。！！曈曈（tóng）：明亮。",
        "translation": "爆竹声里旧岁过去，春风送来暖意，人们举杯喝屠苏。太阳明亮照着千家万户，家家户户把新桃符换下旧桃符。",
    },
    "清明": {
        "author": "杜牧",
        "dynasty": "唐",
        "lines": ["清明时节雨纷纷，", "路上行人欲断魂。", "借问酒家何处有？", "牧童遥指杏花村。"],
        "annotation": "断魂：形容愁苦。！！杏花村：村名。",
        "translation": "清明时节细雨纷纷，路上行人心里惆怅。问哪里有酒家，牧童远远指向杏花村。",
    },
    "九月九日忆山东兄弟": {
        "author": "王维",
        "dynasty": "唐",
        "lines": ["独在异乡为异客，", "每逢佳节倍思亲。", "遥知兄弟登高处，", "遍插茱萸少一人。"],
        "annotation": "茱萸（zhū yú）：一种植物。！！登高：重阳习俗。",
        "translation": "我独自在外地做客，每逢节日更想家。想象兄弟们登高插茱萸时，会少我一个人。",
    },
}


def poem_item(key: str, task: str, best_answer: str) -> Dict[str, Any]:
    p = POEMS[key]
    return item(
        key.replace("·", " "),
        "ancient_poem",
        p["lines"],
        task,
        best_answer,
        author=p["author"],
        dynasty=p["dynasty"],
        annotation=p.get("annotation", ""),
        translation=p.get("translation", ""),
    )


def make_unit(unit_no: int) -> List[Dict[str, Any]]:
    start_week = 2 * (unit_no - 1) + 1
    w1, w2 = start_week, start_week + 1

    # 单元主题与课本复习标题池（只用标题+“画面概述”，避免照抄）
    unit_cfg = {
        1: {
            "themes": [
                "春风把世界擦亮", "燕子剪影", "荷叶大圆盘", "昆虫小档案", "春游路线图", "植物朋友观察记",
                "春天的颜色盒", "池塘微电影", "树梢的消息", "风里有花香", "园地里的小本领", "故事会：春天开场",
            ],
            "textbook": [
                ("燕子", ["乌黑羽毛、剪刀尾巴、轻快翅膀（外形抓特点）。", "微风细雨里，柔柳与花草“赶集”般热闹（春景总分）。"]),
                ("荷花", ["荷叶挨挨挤挤像碧绿的大圆盘（比喻很像）。", "白荷花从“圆盘”间冒出来，像在探头看世界（拟人）。"]),
                ("昆虫备忘录", ["把小昆虫写成“小名片”：外形、动作、特点。", "写清楚：在哪里看见？它在做什么？"]),
                ("口语交际：春游去哪儿玩", ["说清地点、理由、准备（条理）。", "结尾加一句邀请：你愿意一起去吗？"]),
                ("习作：我的植物朋友", ["先总说“它像什么朋友”，再写叶、花、香、颜色（总分）。", "加上一个小发现：今天它有什么变化？"]),
            ],
            "poems": ["绝句·迟日江山丽", "惠崇春江晚景", "三衢道中"],
        },
        2: {
            "themes": [
                "不守株也能有收获", "陶罐的温柔", "鹿角的烦恼", "池子与河流", "班干部轮流吗", "看图写清楚",
                "寓言里的灯泡", "换个角度", "小故事大道理", "园地里的辩论", "一句话说服人", "我会讲故事",
            ],
            "textbook": [
                ("守株待兔", ["有人捡到一次兔子，就天天等“好运”。", "寓意：勤劳才可靠，侥幸靠不住。"]),
                ("陶罐和铁罐", ["铁罐爱逞强，陶罐很谦和。", "时间会把真相“挖出来”：各有用处才长久。"]),
                ("鹿角和鹿腿", ["好看的角让鹿得意，细长腿救了命。", "看人看物别只看外表，要看“用处”。"]),
                ("池子与河流", ["池子骄傲又安静，河流忙碌却清新。", "流动带来活力，停住容易变坏。"]),
                ("口语交际：轮流制", ["先表态，再举例，最后补一句建议（条理）。", "学会用“我认为/因为/所以”。"]),
                ("习作：看图写一写", ["先写时间地点人物，再写动作表情（把句子写具体）。", "最后写一句心情或收获。"]),
            ],
            "poems": ["元日", "清明"],
        },
        3: {
            "themes": [
                "节日的声音", "纸从哪里来", "桥上的石狮子", "名画小讲解", "我做节日策划", "园地里的传统",
                "清明的小雨点", "重阳的茱萸香", "把说明写明白", "总分段练习", "我来当小讲解员", "灯火与烟火",
            ],
            "textbook": [
                ("元日", ["爆竹一响，旧岁走开；春风一吹，新年走来。", "抓意象：爆竹、屠苏、桃符。"]),
                ("清明", ["雨丝像细线，牵出一丝乡愁。", "抓画面：雨、行人、牧童、杏花村。"]),
                ("九月九日忆山东兄弟", ["一句“倍思亲”，把想念写得更深。", "抓动作：登高、插茱萸。"]),
                ("纸的发明", ["写“先后顺序”：先…再…然后…最后…", "抓关键词：材料、方法、用途。"]),
                ("赵州桥", ["总说它“雄伟”，再分写：拱、栏板、石狮子（总分）。", "用数字写具体：长度、宽度。"]),
                ("一幅名扬中外的画", ["先写整体，再写局部（总分）。", "把人物动作写清楚：谁在做什么。"]),
            ],
            "poems": ["元日", "清明", "九月九日忆山东兄弟"],
        },
        4: {
            "themes": [
                "花钟的时刻表", "蜜蜂的路标", "小虾的透明衣", "我做小实验", "园地里的观察", "一段写清楚",
                "用拟人写花开", "用比喻写动作", "我的实验记录", "一句话加细节", "科学小记者", "花园里的音符",
            ],
            "textbook": [
                ("花钟", ["清晨、正午、傍晚，不同的花像在“按时打卡”。", "写法：用动作词写花开（吹起、绽开、苏醒）。"]),
                ("蜜蜂", ["小蜜蜂飞远了还能找到家（方向感）。", "写法：用“先…再…”写过程。"]),
                ("小虾", ["小虾透明，游动像小箭。", "写法：抓特点+动作词（蹿、躲、停）。"]),
                ("习作：我做了一项小实验", ["开头交代材料，过程写顺序，结尾写发现。", "句子写具体：颜色、气味、声音。"]),
            ],
            "poems": ["绝句·迟日江山丽"],
        },
        5: {
            "themes": [
                "宇宙的提问箱", "我变成一棵树", "铅笔的梦想", "尾巴的秘密", "想象开关", "把想象写具体",
                "会走路的云", "会说话的影子", "奇妙的结尾", "习作小锦囊", "园地里的修辞", "我的脑洞星球",
            ],
            "textbook": [
                ("宇宙的另一边", ["用“那么…吗？”把想象打开。", "写法：提问开头，越问越有趣。"]),
                ("我变成了一棵树", ["一会儿想躲，一会儿想分享（心情变化）。", "写法：写动作+心理，让故事更真。"]),
                ("一支铅笔的梦想", ["铅笔想当梯子、桥、翅膀（想象清单）。", "写法：排比让画面更密。"]),
                ("尾巴它有一只猫", ["反过来说也成立，童趣就出来了。", "写法：颠倒句式+夸张。"]),
                ("习作：奇妙的想象", ["先定一个“变身”，再写三件有趣的事。", "结尾写一句：我真想再来一次。"]),
            ],
            "poems": ["三衢道中"],
        },
        6: {
            "themes": [
                "水墨画的颜色", "剃头大师来啦", "肥皂泡飞起", "我不能失信", "人物特点卡", "园地里的口气",
                "动作描写训练", "语言描写训练", "外貌描写训练", "总分段：写一个人", "童年的小电影", "我最像谁",
            ],
            "textbook": [
                ("童年的水墨画", ["一笔绿、一点红，把溪边写得像画。", "写法：颜色+声音+动作（扑腾一声）。"]),
                ("剃头大师", ["吹牛的“大师”反成笑话（反差）。", "写法：语言描写+动作描写。"]),
                ("肥皂泡", ["泡泡轻轻飞，像小气球，也像彩虹。", "写法：比喻+颜色。"]),
                ("我不能失信", ["答应别人的事要做到。", "写法：对话写清楚人物态度。"]),
                ("习作：身边那些有特点的人", ["先总说“他最特别的地方”，再举两件事证明。", "结尾写一句：我很佩服他/她。"]),
            ],
            "poems": ["九月九日忆山东兄弟"],
        },
        7: {
            "themes": [
                "世界像个放大镜", "海底的灯光", "火烧云变变变", "劝告要温柔", "熊猫观察员", "园地里的说明",
                "写景总分段", "颜色变化记", "说明文三步", "修辞小练习", "一个比喻一幅画", "我的小百科",
            ],
            "textbook": [
                ("我们奇妙的世界", ["清晨的粉红到蔚蓝，像魔术。", "写法：总说+分写（总分）。"]),
                ("海底世界", ["海底有发光的鱼，也有像小伞的水母。", "写法：分类说明（比如、还有、特别是）。"]),
                ("火烧云", ["云一会儿像狮子，一会儿像大狗（变化快）。", "写法：比喻+排比。"]),
                ("口语交际：劝告", ["先肯定，再建议，语气要温柔。", "句式：我觉得…不如…好吗？"]),
                ("习作：国宝大熊猫", ["外形（黑白）、习性（爱吃竹子）、特点（慢吞吞）。", "写法：总分+小标题。"]),
            ],
            "poems": ["清明"],
        },
        8: {
            "themes": [
                "慢慢做也很酷", "方帽子店奇遇", "漏的谜团", "枣核小小大大", "趣味故事会", "想象真有趣",
                "一句话讲清楚", "对话让人物活", "结尾要有回声", "园地里的好办法", "我会改编故事", "收尾的掌声",
            ],
            "textbook": [
                ("慢性子裁缝和急性子顾客", ["顾客急，裁缝慢，笑点在反差。", "写法：对话+动作。"]),
                ("方帽子店", ["方帽子硬撑，圆帽子更舒服。", "写法：夸张+对比。"]),
                ("漏", ["一句“漏”，把紧张变成搞笑。", "写法：误会推动情节。"]),
                ("枣核", ["小东西也有大作用（出人意料）。", "写法：开头设问，结尾回扣。"]),
                ("口语交际：趣味故事会", ["讲清楚：谁—做什么—结果。", "声音和表情也算“内容”。"]),
                ("习作：这样想象真有趣", ["把普通东西变“有生命”。", "写法：拟人+夸张。"]),
            ],
            "poems": ["九月九日忆山东兄弟"],
        },
    }

    cfg = unit_cfg[unit_no]
    themes = cfg["themes"]
    textbook = cfg["textbook"]
    poem_keys = cfg.get("poems", [])

    def pick(seq: List[Any], idx: int) -> Any:
        return seq[idx % len(seq)]

    data: List[Dict[str, Any]] = []
    # 12 天：周一到周六 * 2
    schedule = [
        ("W1D1", ["textbook", "modern_prose", "poem", "daily"]),
        ("W1D2", ["textbook", "story_legend", "classics", "daily"]),
        ("W1D3", ["modern_prose", "children_poem", "classical_chinese", "daily"]),
        ("W1D4", ["textbook", "modern_prose", "story_legend", "daily"]),
        ("W1D5", ["textbook", "poem", "classics", "daily"]),
        ("W1D6", ["modern_prose", "story_legend", "children_poem", "daily"]),
        ("W2D1", ["textbook", "modern_prose", "classical_chinese", "daily"]),
        ("W2D2", ["textbook", "story_legend", "poem", "daily"]),
        ("W2D3", ["modern_prose", "textbook", "classics", "daily"]),
        ("W2D4", ["modern_prose", "story_legend", "children_poem", "daily"]),
        ("W2D5", ["textbook", "modern_prose", "classical_chinese", "daily"]),
        ("W2D6", ["textbook", "modern_prose", "poem", "daily"]),
    ]

    def make_textbook(i: int) -> Dict[str, Any]:
        title, bullets = pick(textbook, i)
        lines = [f"（画面）{bullets[0]}", f"（写法）{bullets[1]}"]
        task = "请从这两句里找出两个“画面词”（颜色/动作/声音都算）。"
        best = "比如：乌黑、剪刀似、轻快；或：碧绿、冒出来、悄悄。"
        return item(f"{title}（课本复习）", "textbook_review", lines, task, best, author="课文")

    def make_modern(i: int) -> Dict[str, Any]:
        scenes = [
            ("校园的风", ["操场边，风把树叶翻成一页页小书。", "铃声一响，笑声像一群小鸟冲出走廊。", "我抬头一看，云朵正在练“变形术”。"]),
            ("河边的发现", ["小溪清清的，像一条会唱歌的绿丝带。", "石头上趴着一只小螺蛳，慢慢地挪动。", "水草一摇一摇，像在跟我打招呼。"]),
            ("雨后的气味", ["雨停了，泥土冒出一股新鲜味儿。", "小水洼里，天空被装进了圆镜子。", "我轻轻一跳，溅起一串亮晶晶的笑。"]),
        ]
        t, ls = pick(scenes, unit_no * 20 + i)
        task = "请把其中一句改写得更具体：加上时间或地点。"
        best = "例如：雨停后在小路上，泥土冒出一股新鲜味儿。"
        return item(t, "modern_prose", ls, task, best, author="原创")

    def make_story(i: int) -> Dict[str, Any]:
        stories = [
            ("会道歉的小松鼠", [
                "小松鼠急着跑，把小兔子的胡萝卜撞掉了。",
                "小兔子皱起眉，小松鼠的耳朵一下红了。",
                "它停下来，说：“对不起，我太着急了。”",
                "小兔子笑了：“没关系，我们一起捡起来！”",
            ], "劝告/道歉"),
            ("河流和石头", [
                "石头说：“我最厉害，我从不改变。”",
                "河流说：“我一直走，但我会带来新鲜的水。”",
                "一年后，石头被阳光晒得发烫，河流却把凉意送到岸边。",
                "石头想了想：原来“改变”也有用。",
            ], "寓意/角度"),
            ("方帽子与圆帽子", [
                "方帽子戴在头上，角角总戳到耳朵。",
                "圆帽子轻轻一扣，像一朵云落在头顶。",
                "方帽子不服气：“我才是规矩！”",
                "圆帽子笑：“舒服也是一种规矩。”",
            ], "童话/反差"),
        ]
        title, ls, _tag = pick(stories, unit_no * 10 + i)
        task = "用“因为……所以……”说一句话，写出故事里的道理。"
        best = "因为只顾逞强不顾实际，所以最后会吃亏。"
        return item(title, "story_legend", ls, task, best, author="改写")

    def make_children_poem(i: int) -> Dict[str, Any]:
        poems = [
            ("云朵的橡皮", ["云朵拿起一块橡皮，", "擦掉一小块蓝。", "太阳悄悄涂上金，", "天空就笑弯了眼。"]),
            ("小花的闹钟", ["牵牛花吹起小喇叭，", "蔷薇把裙摆抖啦抖。", "睡莲揉揉惺忪眼，", "花园准时开早会。"]),
            ("泡泡旅行", ["泡泡轻轻往上跑，", "跑到树梢停一停。", "风来拍拍它的背，", "它就飞进彩虹里。"]),
        ]
        title, ls = pick(poems, unit_no * 10 + i)
        task = "拍手读两遍，找出一处像“拟人”的写法。"
        best = ""
        return item(title, "children_poem", ls, task, best, author="原创")

    def make_classics(i: int) -> Dict[str, Any]:
        rules = [
            ("弟子规两句", ["冠必正，纽必结。", "置朝夕，勿乱顿。"], "关于整理"),
            ("论语一句", ["学而时习之，不亦说乎。"], "关于复习"),
            ("增广一句", ["书到用时方恨少。"], "关于积累"),
        ]
        title, ls, _tag = pick(rules, unit_no * 10 + i)
        ann = "挑一个词解释：冠/纽/顿/说。"
        task = "把这句话换成自己的话说一说。"
        best = "我会把东西放整齐，按时复习，学到用时不着急。"
        return item(title, "classics", ls, task, best, author="古文名句", annotation=ann)

    def make_classical(i: int) -> Dict[str, Any]:
        small = [
            ("小古文：孔融让梨", ["孔融四岁，能让梨。", "取小者，长者先。"], "孔融让梨的故事很有名"),
            ("小古文：司马光", ["光少时，见群儿戏。", "一儿登瓮，足跌没水。"], "司马光砸缸的开端"),
        ]
        title, ls, _tag = pick(small, unit_no * 10 + i)
        ann = "少时：小时候。！！瓮：大缸。"
        trans = "孔融小时候把大的梨让给哥哥们，自己拿小的。/ 司马光小时候看见孩子们玩耍，有个孩子掉进大缸里。"
        task = "用一句话说说你学到了什么品质。"
        best = "我学到要谦让/遇事冷静想办法。"
        return item(title, "classical_chinese", ls, task, best, author="古文", dynasty="古代", annotation=ann, translation=trans)

    def make_daily(i: int) -> Dict[str, Any]:
        # 好词：尽量含画面/动作/颜色/四字词，并用括号注音提示生字
        words_pool = [
            "烂漫（làn màn）", "轻快（qīng kuài）", "碧绿（bì lǜ）", "蔚蓝（wèi lán）",
            "若隐若现（ruò yǐn ruò xiàn）", "欢天喜地（huān tiān xǐ dì）",
            "蹦蹦跳跳（bèng bèng tiào tiào）", "叮咚（dīng dōng）", "闪闪发光（shǎn shǎn fā guāng）",
            "慢条斯理（màn tiáo sī lǐ）", "专心致志（zhuān xīn zhì zhì）",
        ]
        good_words = [words_pool[(unit_no * 7 + i + k) % len(words_pool)] for k in range(6)]
        good_sents = [
            "太阳像一个红红的大火球。（比喻很像，画面亮。）",
            "小溪叮咚叮咚，像在唱歌。（拟人/比喻都有趣。）",
        ]
        sections = [
            ("好词", good_words),
            ("好句", good_sents),
        ]
        task = "（应用）选一个四字词语，写一句话，要写清楚“在哪儿/在干什么”。"
        ans = "我在操场上专心致志地练跳绳，汗珠亮闪闪的。"
        return daily_accumulation(sections, task, ans)

    for i, (_tag, blocks) in enumerate(schedule):
        week = w1 if i < 6 else w2
        day = (i % 6) + 1
        theme = themes[i]

        content: List[Dict[str, Any]] = []
        for b in blocks:
            if b == "textbook":
                content.append(make_textbook(i))
            elif b == "modern_prose":
                content.append(make_modern(i))
            elif b == "story_legend":
                content.append(make_story(i))
            elif b == "children_poem":
                content.append(make_children_poem(i))
            elif b == "classics":
                content.append(make_classics(i))
            elif b == "classical_chinese":
                content.append(make_classical(i))
            elif b == "poem":
                key = pick(poem_keys, i) if poem_keys else "绝句·迟日江山丽"
                # 古诗任务：背诵类不填答案，理解类可给答案
                task = "读一读，找出诗里写到的两种颜色。"
                best = "比如：碧绿、金黄等。"
                if unit_no in (1, 3, 7) and "绝句" in key:
                    task = "背一背这首诗。"
                    best = ""
                content.append(poem_item(key, task, best))
            elif b == "daily":
                content.append(make_daily(i))
            else:
                raise ValueError(f"unknown block: {b}")

        data.append(day_block(week, day, theme, content))

    return data


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for unit in range(1, 9):
        out_path = OUT_DIR / f"3年级下册{unit}单元.txt"
        data = make_unit(unit)
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已生成：{out_path} (days={len(data)})")


if __name__ == "__main__":
    main()

