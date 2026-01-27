#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把“无拼音/下学期/3年级”现有 1-8 单元内容，转换为“有拼音_重写版”格式并补齐拼音字段。

输入：
  内容/无拼音/下学期/3年级/3年级下册{1..8}单元.txt

输出（新生成/覆盖同名文件）：
  内容/有拼音_重写版/下学期/3年级/3年级下册{1..8}单元.txt

转换规则（与当前 2-8 单元校验规则保持一致）：
1) 字段映射：
   - best_answer -> taskAnswer（若 taskAnswer 为空时）
2) 拼音生成：
   - 对所有 text/title/task/... 中“出现的汉字”（包含括号里的汉字）生成带声调拼音（空格分隔）
3) 体裁括号清理（title）：
   - 仅移除（短文/小短文/小故事/小寓言/极短）
4) 不可书面表达任务不填答案：
   - 背诵/背一背/背给…听/读…遍/跟读/拍手读/做动作/模仿动作 等 → taskAnswer 置空
5) term 统一：
   - 目录为“下学期”，统一 term=1
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pypinyin import Style, lazy_pinyin


ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "内容" / "无拼音" / "下学期" / "3年级"
OUT_DIR = ROOT / "内容" / "有拼音_重写版" / "下学期" / "3年级"

GENRE_PARENS = {"短文", "小短文", "小故事", "小寓言", "极短"}


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


def _get(obj: Dict[str, Any], key: str, default: str = "") -> str:
    v = obj.get(key, default)
    return v if isinstance(v, str) else default


def convert_item(old: Dict[str, Any]) -> Dict[str, Any]:
    typ = _get(old, "type")
    title = strip_genre_parens(_get(old, "title"))

    task = _get(old, "task")
    task_answer = _get(old, "taskAnswer")
    best_answer = _get(old, "best_answer")
    if (not task_answer.strip()) and best_answer.strip():
        task_answer = best_answer

    # 非书面任务：答案置空
    if is_non_written_task(task):
        task_answer = ""

    d: Dict[str, Any] = {
        "title": title,
        "titlePinyin": py(title),
        "type": typ,
        "author": _get(old, "author"),
        "authorPinyin": py(_get(old, "author")),
        "dynasty": _get(old, "dynasty"),
        "dynastyPinyin": py(_get(old, "dynasty")),
        "contentObject": [],
        "annotation": _get(old, "annotation"),
        "annotationPinyin": py(_get(old, "annotation")),
        "translation": _get(old, "translation"),
        "translationPinyin": py(_get(old, "translation")),
        "appreciation": _get(old, "appreciation"),
        "appreciationPinyin": py(_get(old, "appreciation")),
        "task": task,
        "taskPinyin": py(task),
        "taskAnswer": task_answer,
        "taskAnswerPinyin": py(task_answer),
    }

    # contentObject 两种结构
    if typ == "daily_accumulation":
        out_sections: List[Dict[str, Any]] = []
        for sec in old.get("contentObject", []) if isinstance(old.get("contentObject"), list) else []:
            if not isinstance(sec, dict):
                continue
            sec_title = strip_genre_parens(_get(sec, "title"))
            content_lines: List[Dict[str, str]] = []
            for ln in sec.get("content", []) if isinstance(sec.get("content"), list) else []:
                if isinstance(ln, dict):
                    t = _get(ln, "text")
                    if t != "":
                        content_lines.append(line(t))
            out_sections.append({"title": sec_title, "titlePinyin": py(sec_title), "content": content_lines})
        d["contentObject"] = out_sections
    else:
        out_lines: List[Dict[str, str]] = []
        for ln in old.get("contentObject", []) if isinstance(old.get("contentObject"), list) else []:
            if isinstance(ln, dict):
                t = _get(ln, "text")
                if t != "":
                    out_lines.append(line(t))
        d["contentObject"] = out_lines

    # 可选字段：保持 2 年级格式（如果你们后续需要）
    if "alignment_mode" in old:
        d["alignment_mode"] = old.get("alignment_mode")
    if "paragraph_indent" in old:
        d["paragraph_indent"] = old.get("paragraph_indent")

    return d


def convert_file(in_path: Path, out_path: Path) -> Dict[str, Any]:
    raw = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"bad json root: {in_path}")

    out: List[Dict[str, Any]] = []
    items = 0

    for day in raw:
        if not isinstance(day, dict):
            continue
        day_out = {
            "grade": 3,
            "term": 1,
            "week": int(day.get("week", 1) or 1),
            "day": int(day.get("day", 1) or 1),
            "theme": _get(day, "theme"),
            "content": [],
        }
        content = day.get("content")
        if isinstance(content, list):
            new_items: List[Dict[str, Any]] = []
            for it in content:
                if isinstance(it, dict):
                    new_items.append(convert_item(it))
                    items += 1
            day_out["content"] = new_items
        out.append(day_out)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent="\t"), encoding="utf-8")
    return {"in": str(in_path), "out": str(out_path), "days": len(out), "items": items}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summaries: List[Dict[str, Any]] = []
    for unit in range(1, 9):
        inp = IN_DIR / f"3年级下册{unit}单元.txt"
        outp = OUT_DIR / f"3年级下册{unit}单元.txt"
        summaries.append(convert_file(inp, outp))

    for s in summaries:
        print(f"已生成：{s['out']}  (days={s['days']}, items={s['items']})")


if __name__ == "__main__":
    main()

