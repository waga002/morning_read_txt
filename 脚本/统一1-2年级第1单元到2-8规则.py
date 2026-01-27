#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 1-2 年级“第1单元”按 2-8 单元的最新规则做一次原地校验+统一（尽量不重写内容）。

覆盖文件：
- 内容/有拼音_重写版/下学期/1年级/1年级下册1单元.txt
- 内容/有拼音_重写版/下学期/2年级/2年级下册1单元.txt

统一目标（与当前 2-8 单元一致）：
1) 标题体裁括号清理：仅移除（短文/小短文/小故事/小寓言/极短）
2) 日积月累：
   - “词语小宝库/好词积累/四字词语(成语)”不搬运到正文（不把 task/答案塞进 content）
   - 若正文已含例句/范例/题目或本身就是例句（句末标点且不是“原句/提示/定义/任务”等行），则：
       - task/taskAnswer 保留在字段里
       - 小标题里去掉“（用…造句/写一句…）”这类任务括号
       - 正文里若出现“范例：...”行，则把它挪回 taskAnswer，并从正文删除（避免读答案）
   - 若正文不含例句（如只有“原句/提示”），且任务确实是写句子类，则：
       - task 放进小标题括号
       - taskAnswer 以“范例：...”追加到正文
       - 清空该条目的 task/taskAnswer 字段（避免学生不读字段）
3) 不可书面表达任务（背诵/背一背/读…遍/跟读/拍手读/做动作等）：taskAnswer 必须为空

注意：仅针对“第1单元”做，避免覆盖你们对 2-8 单元的人工调整。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pypinyin import Style, lazy_pinyin


ROOT = Path(__file__).resolve().parents[1]

FILES = [
    ROOT / "内容" / "有拼音_重写版" / "下学期" / "1年级" / "1年级下册1单元.txt",
    ROOT / "内容" / "有拼音_重写版" / "下学期" / "2年级" / "2年级下册1单元.txt",
]

GENRE_PARENS = {"短文", "小短文", "小故事", "小寓言", "极短"}

NO_MOVE_DAILY_TITLES = {
    "词语小宝库",
    "好词积累",
    "四字词语/成语",
    "四字词语",
    "成语",
}

NON_EXAMPLE_PREFIXES = (
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


def _only_han(s: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fff]", s or ""))


def py(text: str) -> str:
    han = _only_han(text)
    if not han:
        return ""
    return " ".join(lazy_pinyin(han, style=Style.TONE))


def line(text: str) -> Dict[str, str]:
    return {"pinyin": py(text), "text": text}


def strip_genre_parens(title: str) -> str:
    if not title:
        return title

    def _repl(m: re.Match[str]) -> str:
        inner = (m.group(1) or "").strip()
        return "" if inner in GENRE_PARENS else m.group(0)

    return re.sub(r"（([^（）]+)）", _repl, title).strip()


def _strip_all_parens(title: str) -> str:
    if not title:
        return ""
    return re.sub(r"（[^（）]*）", "", title).strip()


def _task_for_title(t: str) -> str:
    t = (t or "").strip()
    return re.sub(r"[。！？!?]+$", "", t)


def is_sentence_task(task: str) -> bool:
    task = task or ""
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
    if re.search(r"写一个.*句", task) or re.search(r"说一个.*句", task):
        return True
    return False


def is_non_written_task(task: str) -> bool:
    t = (task or "").strip()
    if not t:
        return False
    if "背诵" in t or "背给" in t or "背一背" in t or "背背" in t or "背会" in t:
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


def _content_has_examples(lines: Any) -> bool:
    if not isinstance(lines, list):
        return False
    for x in lines:
        if not isinstance(x, dict):
            continue
        txt = (x.get("text") or "").strip()
        if not txt:
            continue
        if any(k in txt for k in ["例句", "范例", "（例句", "（范例", "题", "题目"]):
            return True
        if any(p in txt for p in ["。", "！", "？"]) and not txt.startswith(NON_EXAMPLE_PREFIXES):
            return True
    return False


def _strip_sentence_task_parens(title: str) -> str:
    """
    去掉标题里“写句子任务”的括号段。
    需要支持括号嵌套（如：照样子写（说）一句）。
    """
    if not title:
        return title
    segs = _top_level_paren_segments(title)
    if not segs:
        return title.strip()
    out: List[str] = []
    last = 0
    for start, end, inner in segs:
        out.append(title[last:start])
        if not is_sentence_task(inner.strip()):
            out.append(title[start : end + 1])
        last = end + 1
    out.append(title[last:])
    return "".join(out).strip()


def _extract_sentence_task_from_title(title: str) -> Optional[str]:
    if not title:
        return None
    segs = _top_level_paren_segments(title)
    cand: Optional[str] = None
    for _, _, inner in segs:
        inner = (inner or "").strip()
        if is_sentence_task(inner):
            cand = inner
    return cand


def _top_level_paren_segments(s: str) -> List[Tuple[int, int, str]]:
    """
    解析中文括号（...）的“顶层括号段”，支持括号嵌套。
    返回 (start_idx, end_idx, inner_text) 列表（start/end 含括号本身）。
    """
    segs: List[Tuple[int, int, str]] = []
    depth = 0
    start: Optional[int] = None
    for i, ch in enumerate(s):
        if ch == "（":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "）":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    inner = s[start + 1 : i]
                    segs.append((start, i, inner))
                    start = None
    return segs


def _pop_example_from_lines(lines: List[Dict[str, Any]]) -> Optional[str]:
    """
    找到并移除第一条“范例：...”行，返回范例文本（去掉前缀）。
    """
    for i, x in enumerate(list(lines)):
        if not isinstance(x, dict):
            continue
        txt = (x.get("text") or "").strip()
        if txt.startswith("范例："):
            ex = txt[len("范例：") :].strip()
            del lines[i]
            return ex
    return None


def _ensure_pinyin_pair(obj: Dict[str, Any], tk: str, pk: str) -> None:
    if tk in obj and pk in obj:
        t = (obj.get(tk) or "").strip()
        obj[pk] = py(t) if t else ""


def _normalize_daily_item(it: Dict[str, Any]) -> int:
    """
    返回变更次数（粗略计数）。
    """
    changed = 0

    co = it.get("contentObject")
    if not isinstance(co, list) or not co:
        return 0

    # 当前脚本假设 1 个 section 为主（实际多为 1）
    for sec in co:
        if not isinstance(sec, dict):
            continue

        sec_title = (sec.get("title") or "").strip()
        base_title = _strip_all_parens(sec_title)
        lines = sec.get("content")
        if not isinstance(lines, list):
            continue

        # 先把正文里的“范例：...”移回 taskAnswer（避免读答案）
        if (it.get("taskAnswer") or "").strip() == "":
            ex = _pop_example_from_lines(lines)
            if ex:
                it["taskAnswer"] = ex
                it["taskAnswerPinyin"] = py(ex)
                changed += 1
        else:
            # 仍然移除正文里的“范例：...”
            ex = _pop_example_from_lines(lines)
            if ex:
                changed += 1

        # 若 task 为空，尝试从标题括号恢复
        if (it.get("task") or "").strip() == "":
            recovered = _extract_sentence_task_from_title(sec_title)
            if recovered:
                # 保证句末句号
                t = recovered if re.search(r"[。！？!?]$", recovered) else f"{recovered}。"
                it["task"] = t
                it["taskPinyin"] = py(t)
                changed += 1
            else:
                # 再尝试从“标题：任务”这种结构恢复（如：仿写：用……写一句……）
                if "：" in sec_title:
                    left, right = sec_title.split("：", 1)
                    right = right.strip()
                    # 右侧看起来像写句子任务才恢复，避免误判
                    if is_sentence_task(right) or any(k in right for k in ["写", "说", "造句", "扩写", "改写", "润色", "仿写"]):
                        t = right if re.search(r"[。！？!?]$", right) else f"{right}。"
                        it["task"] = t
                        it["taskPinyin"] = py(t)
                        # 同时把 section 标题收敛回左侧（避免标题携带任务）
                        sec["title"] = left.strip()
                        sec["titlePinyin"] = py(sec["title"])
                        changed += 1

        # 不可书面任务：答案必须为空
        if is_non_written_task(it.get("task", "")):
            if (it.get("taskAnswer") or "").strip():
                it["taskAnswer"] = ""
                it["taskAnswerPinyin"] = ""
                changed += 1

        # 词语列表类：不搬运到正文；标题去掉任务括号
        if base_title in NO_MOVE_DAILY_TITLES:
            new_title = _strip_sentence_task_parens(sec_title)
            if new_title != sec_title:
                sec["title"] = new_title
                sec["titlePinyin"] = py(new_title)
                changed += 1
            sec["content"] = lines
            continue

        # 判断正文是否已有例句
        has_examples = _content_has_examples(lines)

        if has_examples:
            # 有例句：任务留在字段；标题去掉任务括号
            new_title = _strip_sentence_task_parens(sec_title)
            if new_title != sec_title:
                sec["title"] = new_title
                sec["titlePinyin"] = py(new_title)
                changed += 1
            sec["content"] = lines
            continue

        # 没有例句：若是写句子类任务，则搬运到标题+正文，并清空字段
        task = (it.get("task") or "").strip()
        task_answer = (it.get("taskAnswer") or "").strip()
        if is_sentence_task(task) and task:
            # 标题加括号（仅加一次）
            inner = _task_for_title(task)
            if f"（{inner}）" not in sec_title:
                sec["title"] = f"{sec_title}（{inner}）"
                sec["titlePinyin"] = py(sec["title"])
                changed += 1
            # 追加范例到正文
            if task_answer:
                lines.append(line(f"范例：{task_answer}"))
                changed += 1
            sec["content"] = lines

            it["task"] = ""
            it["taskPinyin"] = ""
            it["taskAnswer"] = ""
            it["taskAnswerPinyin"] = ""
            changed += 1
        else:
            # 非写句子类：不搬
            sec["content"] = lines

    it["contentObject"] = co
    return changed


def normalize_file(path: Path) -> Tuple[int, int]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return 0, 0

    changed = 0
    items = 0

    for day in raw:
        if not isinstance(day, dict):
            continue
        # 下学期统一 term=1
        day["term"] = 1
        content = day.get("content")
        if not isinstance(content, list):
            continue
        for it in content:
            if not isinstance(it, dict):
                continue
            items += 1

            # 体裁括号清理（title）
            if "title" in it:
                new_title = strip_genre_parens(it.get("title", ""))
                if new_title != it.get("title", ""):
                    it["title"] = new_title
                    changed += 1
                if "titlePinyin" in it:
                    it["titlePinyin"] = py(it["title"])

            # 不可书面任务：清空答案
            if is_non_written_task(it.get("task", "")):
                if (it.get("taskAnswer") or "").strip():
                    it["taskAnswer"] = ""
                    it["taskAnswerPinyin"] = ""
                    changed += 1

            # 日积月累专项统一
            if it.get("type") == "daily_accumulation":
                changed += _normalize_daily_item(it)

            # 最后统一拼音字段（只对存在的配对字段）
            for tk, pk in [
                ("task", "taskPinyin"),
                ("taskAnswer", "taskAnswerPinyin"),
                ("author", "authorPinyin"),
                ("dynasty", "dynastyPinyin"),
                ("annotation", "annotationPinyin"),
                ("translation", "translationPinyin"),
                ("appreciation", "appreciationPinyin"),
            ]:
                _ensure_pinyin_pair(it, tk, pk)

            # contentObject 行的拼音（含 daily 的二层 content）
            if it.get("type") == "daily_accumulation":
                for sec in it.get("contentObject", []) if isinstance(it.get("contentObject"), list) else []:
                    if not isinstance(sec, dict):
                        continue
                    if "title" in sec and "titlePinyin" in sec:
                        sec["titlePinyin"] = py(sec["title"])
                    if isinstance(sec.get("content"), list):
                        for ln in sec["content"]:
                            if isinstance(ln, dict) and "text" in ln and "pinyin" in ln:
                                ln["pinyin"] = py((ln.get("text") or "").strip())
            else:
                if isinstance(it.get("contentObject"), list):
                    for ln in it["contentObject"]:
                        if isinstance(ln, dict) and "text" in ln and "pinyin" in ln:
                            ln["pinyin"] = py((ln.get("text") or "").strip())

    if changed:
        path.write_text(json.dumps(raw, ensure_ascii=False, indent="\t"), encoding="utf-8")
    return changed, items


def main() -> None:
    for p in FILES:
        if not p.exists():
            print(f"跳过（不存在）：{p}")
            continue
        changed, items = normalize_file(p)
        print(f"{p.relative_to(ROOT)}: items={items}, changes={changed}")


if __name__ == "__main__":
    main()

