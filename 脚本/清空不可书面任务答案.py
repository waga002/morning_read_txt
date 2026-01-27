#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空“不可书面表达”的任务答案（在现有 JSON 文件上原地修复）。

适用：背诵/背一背/背给…听/读…遍/跟读/拍手读/做动作等任务
规则：仅清空 taskAnswer / taskAnswerPinyin，不改动 task 本身，也不改动正文 content。

默认处理目录：
  内容/有拼音_重写版/下学期/2年级/2年级下册{2..8}单元.txt
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = ROOT / "内容" / "有拼音_重写版" / "下学期" / "2年级"


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


def fix_file(path: Path) -> int:
    raw = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    if not isinstance(raw, list):
        return 0

    for day in raw:
        if not isinstance(day, dict):
            continue
        content = day.get("content")
        if not isinstance(content, list):
            continue
        for it in content:
            if not isinstance(it, dict):
                continue
            task = it.get("task", "")
            if is_non_written_task(task):
                if (it.get("taskAnswer") or "").strip() or (it.get("taskAnswerPinyin") or "").strip():
                    it["taskAnswer"] = ""
                    it["taskAnswerPinyin"] = ""
                    changed += 1

    if changed:
        path.write_text(json.dumps(raw, ensure_ascii=False, indent="\t"), encoding="utf-8")
    return changed


def main() -> None:
    total = 0
    for unit in range(2, 9):
        p = TARGET_DIR / f"2年级下册{unit}单元.txt"
        n = fix_file(p)
        total += n
        print(f"{p.name}: 清空 {n} 条")
    print(f"完成：共清空 {total} 条")


if __name__ == "__main__":
    main()

