#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「1年级可用晨读版」内容（在不破坏原文件的前提下输出到新目录）。

做的事情（偏保守、可回滚）：
1) 修复已知明显错别字/不合适内容（根据仓库内既有报告补丁）
2) 将明显不适合一年级的“写一句话”类任务改为“说一句话”
3) 将括号里的解释（如“（要珍惜时间）”）从 text 中裁掉，只保留主句（降低难度 + 拼音更稳）
4) 自动重算/修复拼音（若拼音含汉字/明显异常/或文本改动过），使用 pypinyin + 声调

输入：
  内容/有拼音/上学期/1年级/*.txt
  内容/有拼音/下学期/1年级/*.txt
输出：
  内容/有拼音_一年级可用版/上学期/1年级/*.txt
  内容/有拼音_一年级可用版/下学期/1年级/*.txt

运行：
  python3 脚本/生成1年级可用晨读版.py
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from pypinyin import Style, lazy_pinyin


ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = ROOT / "内容" / "有拼音"
OUTPUT_ROOT = ROOT / "内容" / "有拼音_一年级可用版"


HAN_RE = re.compile(r"[\u4e00-\u9fff]")
PAREN_RE = re.compile(r"（[^）]*）|\([^)]*\)")


@dataclass
class Change:
    file: str
    where: str
    before: str
    after: str


def extract_chinese(text: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fff]", text or ""))


def to_pinyin_tone(text: str) -> str:
    chinese = extract_chinese(text)
    if not chinese:
        return ""
    parts = lazy_pinyin(chinese, style=Style.TONE)
    return " ".join(parts)


def pinyin_has_han(pinyin: str) -> bool:
    return bool(HAN_RE.search(pinyin or ""))


def strip_parenthetical_explain(text: str) -> str:
    """
    把“（...）”这种解释去掉，尽量保留主句。
    例：'春雨贵如油。（很宝贵）' -> '春雨贵如油。'
    """
    if not text:
        return text
    # 仅当原句确实包含括号说明时才处理（避免误伤诗句里的正常标点）
    if "（" not in text and "(" not in text:
        return text

    stripped = PAREN_RE.sub("", text).strip()
    # 如果括号内容在句末，常会留下“，”“、”之类的尾巴，这里再做一次温和清理
    stripped = re.sub(r"[，,、]\s*$", "", stripped)
    # 清理重复标点（常见于 “）。/），” 这类结构裁剪后）
    stripped = re.sub(r"。{2,}", "。", stripped)
    stripped = re.sub(r"，{2,}", "，", stripped)
    stripped = re.sub(r"、{2,}", "、", stripped)
    return stripped


def normalize_task(text: str) -> str:
    if not text:
        return text
    # 一年级尽量避免“写一句话”
    text = text.replace("写一句话", "说一句话")
    text = text.replace("写一写", "说一说")
    # 更口语、更低门槛
    text = text.replace("写一句", "说一句")
    return text


def apply_known_fixes(s: str) -> str:
    if not s:
        return s

    # 明显错别字/不合适内容（来自 脚本/1年级内容不合适问题补充报告.md）
    s = s.replace("忘记吃猪肉。", "忘记吃午饭。")
    s = s.replace("撑着重重的货。", "载着重重的货。")
    s = s.replace("坡下还着一只鹅。", "坡下还有一只鹅。")
    s = s.replace("弯鹅火了", "坡上鹅火了")
    s = s.replace("汪汪大笑", "汪汪叫起来")
    s = s.replace("先跑来木头", "先找来木头")
    s = s.replace("看玩故事", "看完故事")

    # 一些明显不当/过激表达，替换为更适合一年级的版本
    s = s.replace("世上没有丑人，只有懒人", "勤快的人，收获多")

    # 过难/过抽象的格言或示例句（一年级晨读口语化）
    s = s.replace("纸上得来终觉浅", "学了要去做")
    s = s.replace("经验丰富的老师耐心地解答学生的问题。", "亲切的老师耐心地回答问题。")

    # 过于抽象/偏难的句子：保守处理（保留主句即可）
    return s


def should_recalc_pinyin(before_text: str, after_text: str, before_pinyin: str) -> bool:
    # 文本变了就重算（避免不一致）
    if (before_text or "") != (after_text or ""):
        return True
    # 拼音里出现了汉字（例如 b扮）一定重算
    if pinyin_has_han(before_pinyin):
        return True
    # 拼音为空但有汉字
    if not (before_pinyin or "").strip() and extract_chinese(after_text):
        return True
    return False


def update_text_and_pinyin(obj: Dict[str, Any], text_key: str, pinyin_key: str, changes: List[Change], file_ref: str, where: str) -> None:
    if text_key not in obj:
        return
    if pinyin_key not in obj:
        return

    before_text = obj.get(text_key, "")
    before_pinyin = obj.get(pinyin_key, "")

    after_text = apply_known_fixes(before_text)
    after_text = normalize_task(after_text) if text_key in ("task", "taskAnswer") else after_text

    # 对“格言/俗语”类经常把解释写进 text 的情况，裁掉括号说明（仅在包含括号时生效）
    if text_key == "text":
        after_text = strip_parenthetical_explain(after_text)

    if after_text != before_text:
        obj[text_key] = after_text
        changes.append(Change(file=file_ref, where=where, before=before_text, after=after_text))

    if should_recalc_pinyin(before_text, after_text, before_pinyin):
        obj[pinyin_key] = to_pinyin_tone(after_text)


def walk_content_items(week_data: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for item in week_data.get("content", []) or []:
        if isinstance(item, dict):
            yield item


def process_file(in_path: Path, out_path: Path) -> Tuple[int, List[Change]]:
    changes: List[Change] = []
    data = json.loads(in_path.read_text(encoding="utf-8"))

    for week_data in data:
        if not isinstance(week_data, dict):
            continue

        file_ref = in_path.name
        week = week_data.get("week", "")
        day = week_data.get("day", "")
        theme = week_data.get("theme", "")
        where_prefix = f"第{week}周第{day}天 - {theme}"

        for content_item in walk_content_items(week_data):
            title = content_item.get("title", "")
            where = f"{where_prefix} / {title}"

            # task / taskPinyin
            if "task" in content_item and "taskPinyin" in content_item:
                before_task = content_item.get("task", "")
                after_task = normalize_task(apply_known_fixes(before_task))
                if after_task != before_task:
                    content_item["task"] = after_task
                    content_item["taskPinyin"] = to_pinyin_tone(after_task)
                    changes.append(Change(file=file_ref, where=f"{where} / task", before=before_task, after=after_task))

            # taskAnswer / taskAnswerPinyin（不强制重算，但文本变动就重算）
            if "taskAnswer" in content_item and "taskAnswerPinyin" in content_item:
                before_a = content_item.get("taskAnswer", "")
                after_a = apply_known_fixes(before_a)
                if after_a != before_a:
                    content_item["taskAnswer"] = after_a
                    content_item["taskAnswerPinyin"] = to_pinyin_tone(after_a)
                    changes.append(Change(file=file_ref, where=f"{where} / taskAnswer", before=before_a, after=after_a))

            # contentObject：两种结构
            for idx, obj in enumerate(content_item.get("contentObject", []) or []):
                if not isinstance(obj, dict):
                    continue

                # 结构1：{text,pinyin}
                if "text" in obj and "pinyin" in obj:
                    update_text_and_pinyin(
                        obj,
                        "text",
                        "pinyin",
                        changes,
                        file_ref,
                        f"{where} / contentObject[{idx}]",
                    )

                # 结构2：{title, content:[{text,pinyin}, ...]}
                if "content" in obj and isinstance(obj.get("content"), list):
                    for jdx, sub in enumerate(obj["content"]):
                        if not isinstance(sub, dict):
                            continue
                        if "text" in sub and "pinyin" in sub:
                            update_text_and_pinyin(
                                sub,
                                "text",
                                "pinyin",
                                changes,
                                file_ref,
                                f"{where} / contentObject[{idx}].content[{jdx}]",
                            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent="\t"), encoding="utf-8")
    return len(changes), changes


def main() -> None:
    input_dirs = [
        INPUT_ROOT / "上学期" / "1年级",
        INPUT_ROOT / "下学期" / "1年级",
    ]
    total_files = 0
    total_changes = 0
    all_changes: List[Change] = []

    for in_dir in input_dirs:
        if not in_dir.exists():
            raise SystemExit(f"未找到输入目录：{in_dir}")

        rel = in_dir.relative_to(INPUT_ROOT)
        out_dir = OUTPUT_ROOT / rel
        out_dir.mkdir(parents=True, exist_ok=True)

        for in_file in sorted(in_dir.glob("*.txt")):
            out_file = out_dir / in_file.name
            c, changes = process_file(in_file, out_file)
            total_files += 1
            total_changes += c
            all_changes.extend(changes)

    # 生成简短变更报告（便于你人工 spot-check）
    report_path = ROOT / "脚本" / "1年级可用晨读版_变更摘要.md"
    lines = []
    lines.append("# 1年级可用晨读版 - 变更摘要")
    lines.append("")
    lines.append(f"- 处理文件数：**{total_files}**")
    lines.append(f"- 发生变更条目数：**{total_changes}**")
    lines.append("")

    # 只列出前 120 条，避免太长
    for ch in all_changes[:120]:
        lines.append(f"- **{ch.file}** / {ch.where}")
        lines.append(f"  - before: {ch.before}")
        lines.append(f"  - after:  {ch.after}")
    if len(all_changes) > 120:
        lines.append("")
        lines.append(f"> 仅展示前 120 条，实际共 {len(all_changes)} 条。")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"完成：输出目录 {OUTPUT_ROOT}")
    print(f"变更摘要：{report_path}")


if __name__ == "__main__":
    main()

