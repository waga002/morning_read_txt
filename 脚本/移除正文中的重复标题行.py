#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移除“正文 content 里重复的标题行”，如：
- 修辞手法：拟人
- 修辞手法：比喻
- 描写手法：外貌/颜色描写

这些信息在对应 section 的 title 里已经有了，放在正文里会影响晨读。

仅原地修改：
- 删除 content / contentObject.content 中满足条件的行
- 不改动其它字段（避免覆盖人工调整）

默认处理：
  内容/有拼音_重写版/下学期/2年级/2年级下册{2..8}单元.txt
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = ROOT / "内容" / "有拼音_重写版" / "下学期" / "2年级"

DROP_RE = re.compile(r"^(修辞手法|描写手法)：.+$")


def _filter_lines(lines: Any) -> Any:
    if not isinstance(lines, list):
        return lines
    out: List[Any] = []
    for x in lines:
        if not isinstance(x, dict):
            out.append(x)
            continue
        txt = (x.get("text") or "").strip()
        if DROP_RE.match(txt):
            # 跳过这行
            continue
        out.append(x)
    return out


def fix_item(it: Dict[str, Any]) -> int:
    changed = 0

    # 普通条目：contentObject 是行列表
    if isinstance(it.get("contentObject"), list) and it.get("type") != "daily_accumulation":
        before = len(it["contentObject"])
        it["contentObject"] = _filter_lines(it["contentObject"])
        after = len(it["contentObject"])
        if after != before:
            changed += before - after

    # 日积月累：contentObject = [{title, content:[...]}, ...]
    if it.get("type") == "daily_accumulation" and isinstance(it.get("contentObject"), list):
        for sec in it["contentObject"]:
            if not isinstance(sec, dict):
                continue
            if isinstance(sec.get("content"), list):
                before = len(sec["content"])
                sec["content"] = _filter_lines(sec["content"])
                after = len(sec["content"])
                if after != before:
                    changed += before - after

    return changed


def fix_file(path: Path) -> int:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return 0

    changed = 0
    for day in raw:
        if not isinstance(day, dict):
            continue
        content = day.get("content")
        if not isinstance(content, list):
            continue
        for it in content:
            if isinstance(it, dict):
                changed += fix_item(it)

    if changed:
        path.write_text(json.dumps(raw, ensure_ascii=False, indent="\t"), encoding="utf-8")
    return changed


def main() -> None:
    total = 0
    for unit in range(2, 9):
        p = TARGET_DIR / f"2年级下册{unit}单元.txt"
        n = fix_file(p)
        total += n
        print(f"{p.name}: 删除 {n} 行")
    print(f"完成：共删除 {total} 行")


if __name__ == "__main__":
    main()

