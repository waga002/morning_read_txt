#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成「2年级下学期」2~8单元的“有拼音_重写版”晨读内容。

来源：内容/有拼音/下学期/2年级/2年级下册{2..8}单元.txt
输出：内容/有拼音_重写版/下学期/2年级/2年级下册{2..8}单元.txt（不覆盖原文件）

按当前标准做两类处理：
1) 标题体裁括号清理：仅移除（短文/小短文/小故事/小寓言/极短）这类体裁标注；其他括号（节选/巩固/再读一段/词句练习等）保留。
2) “写句子类”任务搬运（仅限 `日积月累`，且排除词语列表板块）：
   - 将 task 放到日积月累内部小标题 `contentObject[*].title` 末尾括号里
   - 将 taskAnswer 以“范例：...”追加到该小标题的 `content` 末尾
   - 将该条目的 task/taskAnswer 置空（避免学生不读字段导致晨读断档）
   说明：`词语小宝库/好词积累/四字词语(成语)` 等词语列表板块不搬运（即使 task 是“造句/说一句”），避免把答案读进正文影响晨读。
3) 不可书面表达的任务不填答案：
   - 如 task 为“背诵/背给…听/读…遍/拍手读/跟读/做动作/模仿动作”等，则将 taskAnswer/taskAnswerPinyin 置空。

运行：
  python3 脚本/批量重写2年级下学期2-8单元.py
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pypinyin import Style, lazy_pinyin


ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "内容" / "有拼音" / "下学期" / "2年级"
OUT_DIR = ROOT / "内容" / "有拼音_重写版" / "下学期" / "2年级"


GENRE_PARENS = {"短文", "小短文", "小故事", "小寓言", "极短"}

# 词语列表类：不把 task/taskAnswer 搬进正文
NO_MOVE_DAILY_TITLES = {
    "词语小宝库",
    "好词积累",
    "四字词语/成语",
    "四字词语",
    "成语",
}


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


def strip_genre_parens(title: str) -> str:
    """
    仅移除体裁标注括号：（短文/小短文/小故事/小寓言/极短）
    其他括号一律保留。
    """
    if not title:
        return title

    def _repl(m: re.Match[str]) -> str:
        inner = (m.group(1) or "").strip()
        return "" if inner in GENRE_PARENS else m.group(0)

    # 支持一个标题里出现多个括号段
    return re.sub(r"（([^（）]+)）", _repl, title).strip()


def _task_for_title(t: str) -> str:
    t = (t or "").strip()
    return re.sub(r"[。！？!?]+$", "", t)


def is_sentence_task(task: str) -> bool:
    task = task or ""
    # 这类晨读里“写句子/造句/扩句/润色/仿写/用某词说一句”等
    if any(
        k in task
        for k in [
            "说一句",
            "写一句",
            "造句",
            "扩写",
            "扩写成",
            "改写",
            "改写成",
            "改写为",
            "润色",
            "照样子",
            "仿写",
            "比喻句",
            "拟人句",
            "拟人的话",
            "扩写得更具体",
            "更生动",
            "更具体",
        ]
    ):
        return True

    # “写一个……句子/说一个……句子”这类（避免把“写一个词”误判）
    if re.search(r"写一个.*句", task) or re.search(r"说一个.*句", task):
        return True

    return False

def is_non_written_task(task: str) -> bool:
    """
    判断任务是否“不可用书面答案表达”。
    规则尽量保守：只匹配纯背诵/纯朗读/做动作这类。
    """
    t = (task or "").strip()
    if not t:
        return False

    # 明确的背诵类
    if "背诵" in t or "背给" in t:
        return True

    # “背一背/背背/背会…”也属于背诵类
    if "背一背" in t or "背背" in t or "背会" in t:
        return True

    # 兜底：以“背”开头且不带明显可回答要求时，也视为背诵类
    if t.startswith("背") and not any(k in t for k in ["解释", "说说", "想一想", "为什么", "怎么", "写出", "找出"]):
        return True

    # 纯朗读/跟读/拍手读（“读一读，找出/写出…”这类可回答的不算）
    if any(k in t for k in ["拍手读", "跟读", "齐读", "大声读", "小声读"]):
        return True

    if re.search(r"读[一二三四五六七八九十0-9]+遍", t):
        # 如果同时包含“找出/写出/说说/想一想/解释/为什么/怎么”等可回答提示，则不视为纯朗读
        if any(k in t for k in ["找出", "写出", "说说", "想一想", "解释", "为什么", "怎么", "哪", "什么", "多少", "几"]):
            return False
        return True

    # 做动作/模仿动作（同时要求“说一说/想一想”的不算纯动作）
    if ("动作" in t and ("模仿" in t or "做" in t)) or "做一做" in t:
        if any(k in t for k in ["说说", "想一想", "解释", "为什么", "怎么"]):
            return False
        return True

    return False


def _strip_all_parens(title: str) -> str:
    """去掉所有中文括号段，得到板块主标题。"""
    if not title:
        return ""
    return re.sub(r"（[^（）]*）", "", title).strip()


def _should_move_daily_sentence_task(section_title: str, task: str) -> bool:
    if not task or not is_sentence_task(task):
        return False
    main_title = _strip_all_parens(section_title)
    if main_title in NO_MOVE_DAILY_TITLES:
        return False
    return True


def _append_example_to_lines(lines: List[Dict[str, Any]], task_answer: str) -> None:
    if not task_answer:
        return
    text = f"范例：{task_answer}"
    if any(isinstance(x, dict) and (x.get("text") or "").strip() == text for x in lines):
        return
    lines.append(line(text))

def _append_task_to_lines(lines: List[Dict[str, Any]], task: str) -> None:
    if not task:
        return
    text = f"任务：{re.sub(r'[。！？!?]+$', '', task.strip())}。"
    if any(isinstance(x, dict) and (x.get("text") or "").strip() == text for x in lines):
        return
    lines.append(line(text))

def _is_rhetoric_section(title: str) -> bool:
    return (title or "").strip().startswith("修辞手法：")

def _content_has_examples(lines: Any) -> bool:
    """
    判断正文是否已经包含“例子/例句/范例/题目”等引导。
    若已包含，则不再把任务硬塞进正文（避免晨读变成“读答案/读任务”）。
    """
    if not isinstance(lines, list):
        return False
    non_example_prefixes = (
        "原句",
        "提示",
        "任务",
        "定义",
        "拟人：",
        "比喻：",
        "用颜色词",
        "用颜色",
        "修辞手法",
        "描写手法",
    )
    for x in lines:
        if not isinstance(x, dict):
            continue
        txt = (x.get("text") or "").strip()
        if not txt:
            continue
        if any(k in txt for k in ["例句", "范例", "（例句", "（范例", "题", "题目"]):
            return True
        # 没有写“范例/例句”，但本身就是例句：包含明显句末标点，且不是“原句/提示/任务/定义”等说明行
        if any(p in txt for p in ["。", "！", "？"]) and not txt.startswith(non_example_prefixes):
            return True
    return False


def _strip_sentence_task_parens(title: str) -> str:
    """
    若标题括号里是“写句子类任务”（如：用……造句/写一句/仿写/扩写/改写等），则移除该括号段。
    例如：好句小箩筐（用因为……所以……造句） -> 好句小箩筐
    """
    if not title:
        return title

    def _repl(m: re.Match[str]) -> str:
        inner = (m.group(1) or "").strip()
        return "" if is_sentence_task(inner) else m.group(0)

    return re.sub(r"（([^（）]+)）", _repl, title).strip()

def _drop_extra_examples(lines: List[Dict[str, Any]], keep_example_text: str) -> List[Dict[str, Any]]:
    """仅保留与 keep_example_text 相同的那条范例，其它以“范例：”开头的行删除。"""
    if not isinstance(lines, list):
        return lines
    keep = f"范例：{keep_example_text}" if keep_example_text else ""
    out: List[Dict[str, Any]] = []
    for x in lines:
        if not isinstance(x, dict):
            continue
        txt = (x.get("text") or "").strip()
        if txt.startswith("范例：") and txt != keep:
            continue
        out.append(x)
    return out


def _rhetoric_name_from_title(title: str) -> str:
    """从“修辞手法：X”里取出 X（去括号）。"""
    t = _strip_all_parens(title)
    if "：" not in t:
        return ""
    return t.split("：", 1)[1].strip()


def _rhetoric_definition(rhetoric_name: str) -> str:
    if rhetoric_name == "拟人":
        return "拟人：就是把东西当作人来写。"
    if rhetoric_name == "比喻":
        return "比喻：就是把一个东西比作另一个东西。"
    # 兜底：未知修辞就不给硬写定义
    return ""


def _build_rhetoric_content(section_title: str, task: str, task_answer: str) -> List[Dict[str, str]]:
    """
    修辞板块统一为：定义 → 任务 → 1条范例
    """
    rhetoric_name = _rhetoric_name_from_title(section_title)
    out: List[Dict[str, str]] = []
    definition = _rhetoric_definition(rhetoric_name)
    if definition:
        out.append(line(definition))
    if task:
        _append_task_to_lines(out, task)
    if task_answer:
        _append_example_to_lines(out, task_answer)
    return out


def ensure_title_pinyin(obj: Dict[str, Any], *, key_title: str = "title", key_pinyin: str = "titlePinyin") -> None:
    if key_title in obj:
        obj[key_pinyin] = py(obj.get(key_title, "") or "")


def transform_item(item: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    返回：新 item、以及变更日志（用于打印摘要）。
    """
    logs: List[str] = []
    it = deepcopy(item)

    # 1) 清理标题里的体裁括号
    old_title = it.get("title", "")
    new_title = strip_genre_parens(old_title)
    if new_title != old_title:
        it["title"] = new_title
        ensure_title_pinyin(it)
        logs.append(f"title体裁括号：{old_title!r} -> {new_title!r}")

    # 2) 写句子类搬运（仅日积月累）
    if it.get("type") == "daily_accumulation":
        task = (it.get("task") or "").strip()
        task_answer = (it.get("taskAnswer") or "").strip()

        co = it.get("contentObject")
        if task and isinstance(co, list) and co:
            moved_any = False
            for sec in co:
                if not isinstance(sec, dict):
                    continue
                sec_title = (sec.get("title") or "").strip()
                if not _should_move_daily_sentence_task(sec_title, task):
                    continue

                lines = sec.get("content")
                if isinstance(lines, list):
                    # 若正文已自带例子/例句/范例/题目，则不搬运（任务保留在 task 字段）
                    if _content_has_examples(lines):
                        # 同时把标题里“（用……造句/写一句/仿写…）”这类任务括号去掉，避免标题塞任务
                        new_sec_title = _strip_sentence_task_parens(sec_title)
                        if new_sec_title != sec_title:
                            sec["title"] = new_sec_title
                            ensure_title_pinyin(sec)
                        continue

                    # “修辞手法：”板块：标题不塞任务；正文顺序=定义→任务→1条范例
                    if _is_rhetoric_section(sec_title):
                        base_title = _strip_all_parens(sec_title)
                        sec["title"] = base_title
                        ensure_title_pinyin(sec)
                        sec["content"] = _build_rhetoric_content(sec_title, task, task_answer)
                    else:
                        sec["title"] = f"{sec_title}（{_task_for_title(task)}）"
                        ensure_title_pinyin(sec)
                        _append_example_to_lines(lines, task_answer)
                        sec["content"] = lines

                moved_any = True
                logs.append(f"日积月累写句子类搬运：{sec_title!r} <- {task!r}")

            if moved_any:
                it["contentObject"] = co
                it["task"] = ""
                it["taskPinyin"] = ""
                it["taskAnswer"] = ""
                it["taskAnswerPinyin"] = ""

    # 3) 不可书面表达的任务：清空 taskAnswer（避免把“背诵内容”当作答案）
    task3 = (it.get("task") or "").strip()
    if is_non_written_task(task3):
        if (it.get("taskAnswer") or "").strip():
            logs.append(f"清空不可书面任务答案：{task3!r}")
        it["taskAnswer"] = ""
        it["taskAnswerPinyin"] = ""

    return it, logs


def transform_file(in_path: Path, out_path: Path) -> Dict[str, Any]:
    raw = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"bad json root (expected list): {in_path}")

    out: List[Dict[str, Any]] = []
    changed_items = 0
    changed_titles = 0
    moved_sentence_tasks = 0

    for day in raw:
        if not isinstance(day, dict):
            out.append(day)
            continue
        day2 = deepcopy(day)
        # 目录已明确为“下学期”，这里统一 term=1（修复个别源文件 term=0 的问题）
        day2["term"] = 1
        content = day2.get("content") or []
        if not isinstance(content, list):
            out.append(day2)
            continue

        new_content: List[Any] = []
        for it in content:
            if not isinstance(it, dict):
                new_content.append(it)
                continue
            new_it, logs = transform_item(it)
            if logs:
                changed_items += 1
                if any(s.startswith("title体裁括号") for s in logs):
                    changed_titles += 1
                if any("写句子类搬运" in s for s in logs):
                    moved_sentence_tasks += 1
            new_content.append(new_it)

        day2["content"] = new_content
        out.append(day2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent="\t"), encoding="utf-8")

    return {
        "in": str(in_path),
        "out": str(out_path),
        "changed_items": changed_items,
        "changed_titles": changed_titles,
        "moved_sentence_tasks": moved_sentence_tasks,
        "days": len(out),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summaries: List[Dict[str, Any]] = []
    for unit in range(2, 9):
        in_path = IN_DIR / f"2年级下册{unit}单元.txt"
        out_path = OUT_DIR / f"2年级下册{unit}单元.txt"
        summaries.append(transform_file(in_path, out_path))

    for s in summaries:
        print(
            f"已生成：{s['out']}  (天数={s['days']}，变更条目={s['changed_items']}，"
            f"体裁标题修正={s['changed_titles']}，日积月累写句子类搬运={s['moved_sentence_tasks']})"
        )


if __name__ == "__main__":
    main()

