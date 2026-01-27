#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验并修复 1-2 年级“有拼音*”内容中的拼音缺失/不一致问题。

核心规则：
- 以 text 字段中的所有汉字为准（包含括号里的汉字）
- pinyin 应为该汉字序列的带声调拼音（以空格分隔）
- text 为空时，对应 pinyin 必须为空

覆盖范围（自动遍历 JSON 结构）：
- contentObject 内的 {text,pinyin} 行（含日积月累的二层 content）
- item 的 title/titlePinyin、task/taskPinyin、taskAnswer/taskAnswerPinyin
- author/authorPinyin、dynasty/dynastyPinyin、annotation/annotationPinyin、translation/translationPinyin、appreciation/appreciationPinyin

默认处理目录（若不存在则跳过）：
- 内容/有拼音_重写版/上学期/1年级
- 内容/有拼音_重写版/上学期/2年级
- 内容/有拼音_重写版/下学期/1年级
- 内容/有拼音_重写版/下学期/2年级
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from pypinyin import Style, lazy_pinyin


ROOT = Path(__file__).resolve().parents[1]


def _only_han(s: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fff]", s or ""))


def _py(text: str) -> str:
    han = _only_han(text)
    if not han:
        return ""
    return " ".join(lazy_pinyin(han, style=Style.TONE))


def _fix_pair(obj: Dict[str, Any], text_key: str, pinyin_key: str) -> int:
    """
    返回修复次数（0/1）。
    """
    text = obj.get(text_key, "")
    pinyin = obj.get(pinyin_key, "")
    text_s = (text or "").strip()
    pinyin_s = (pinyin or "").strip()

    if not text_s:
        if pinyin_s:
            obj[pinyin_key] = ""
            return 1
        return 0

    expected = _py(text_s)
    if expected != pinyin_s:
        obj[pinyin_key] = expected
        return 1
    return 0


def _fix_line_obj(line_obj: Dict[str, Any]) -> int:
    # 只处理标准行结构
    if "text" in line_obj and "pinyin" in line_obj:
        return _fix_pair(line_obj, "text", "pinyin")
    return 0


def _iter_grade_dirs() -> Iterable[Path]:
    base = ROOT / "内容" / "有拼音_重写版"
    for term_dir in ["上学期", "下学期"]:
        for grade_dir in ["1年级", "2年级"]:
            p = base / term_dir / grade_dir
            if p.exists() and p.is_dir():
                yield p


def _iter_json_files(d: Path) -> List[Path]:
    return sorted([p for p in d.glob("*.txt") if p.is_file()])


def _fix_daily_content_object(obj: Dict[str, Any]) -> int:
    """
    daily_accumulation: contentObject = [{title,titlePinyin,content:[{text,pinyin}, ...]}, ...]
    """
    changed = 0
    co = obj.get("contentObject")
    if not isinstance(co, list):
        return 0
    for sec in co:
        if not isinstance(sec, dict):
            continue
        if "title" in sec and "titlePinyin" in sec:
            changed += _fix_pair(sec, "title", "titlePinyin")
        content = sec.get("content")
        if isinstance(content, list):
            for ln in content:
                if isinstance(ln, dict):
                    changed += _fix_line_obj(ln)
    return changed


def _fix_item(obj: Dict[str, Any]) -> int:
    changed = 0

    # 标题/任务/答案/作者等字段
    for tk, pk in [
        ("title", "titlePinyin"),
        ("task", "taskPinyin"),
        ("taskAnswer", "taskAnswerPinyin"),
        ("author", "authorPinyin"),
        ("dynasty", "dynastyPinyin"),
        ("annotation", "annotationPinyin"),
        ("translation", "translationPinyin"),
        ("appreciation", "appreciationPinyin"),
    ]:
        if tk in obj and pk in obj:
            changed += _fix_pair(obj, tk, pk)

    # contentObject：两种形态
    typ = obj.get("type", "")
    if typ == "daily_accumulation":
        changed += _fix_daily_content_object(obj)
    else:
        co = obj.get("contentObject")
        if isinstance(co, list):
            for ln in co:
                if isinstance(ln, dict):
                    changed += _fix_line_obj(ln)

    return changed


def _fix_file(path: Path) -> Tuple[int, int]:
    """
    返回：(修复字段次数, 处理的 item 数)
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return 0, 0

    changed = 0
    items = 0

    for day in raw:
        if not isinstance(day, dict):
            continue
        content = day.get("content")
        if not isinstance(content, list):
            continue
        for it in content:
            if not isinstance(it, dict):
                continue
            items += 1
            changed += _fix_item(it)

    if changed:
        path.write_text(json.dumps(raw, ensure_ascii=False, indent="\t"), encoding="utf-8")

    return changed, items


def main() -> None:
    total_changed = 0
    total_items = 0
    total_files = 0

    for d in _iter_grade_dirs():
        for f in _iter_json_files(d):
            total_files += 1
            changed, items = _fix_file(f)
            total_changed += changed
            total_items += items
            print(f"{f.relative_to(ROOT)}: items={items}, fixes={changed}")

    print(f"完成：files={total_files}, items={total_items}, fixes={total_changed}")


if __name__ == "__main__":
    main()

