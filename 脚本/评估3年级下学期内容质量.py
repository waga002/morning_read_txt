#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对 3 年级下学期（无拼音）晨读内容做“逐篇”质量评估。

“每篇”的定义：每一天（week/day）下 content 数组里的每一个条目（content_item）。

输出：
1) TSV 明细表：汇总/3年级/内容质量评估表_3年级下学期_无拼音.tsv
2) MD 概览报告：汇总/3年级/内容质量评估报告_3年级下学期_无拼音.md

评估目标：帮助快速定位需要人工复核的条目（缺字段、过短、任务/答案质量弱、疑似重复等）。
这是启发式规则，不替代人工审校。
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "内容" / "无拼音" / "下学期" / "3年级"
OUTPUT_TSV = BASE_DIR / "汇总" / "3年级" / "内容质量评估表_3年级下学期_无拼音.tsv"
OUTPUT_MD = BASE_DIR / "汇总" / "3年级" / "内容质量评估报告_3年级下学期_无拼音.md"


UNIT_FILES = [INPUT_DIR / f"3年级下册{i}单元.txt" for i in range(1, 9)]


READ_LEVEL_BY_BLOCK_INDEX = {
    1: "精读",
    2: "泛读",
    3: "泛读",
    4: "精读",
}


SHORT_TYPES = {"ancient_poem", "classical_chinese", "classic_recitation"}


def _safe_str(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x.strip()
    return str(x).strip()


def extract_texts_from_content_object(content_object: Any) -> List[str]:
    """
    兼容两种结构：
    1) [{"text": "..."}...]
    2) [{"title": "...", "content": [{"text": "..."}]}...]  (常见于 daily_accumulation)
    """
    texts: List[str] = []
    if not content_object:
        return texts
    if not isinstance(content_object, list):
        return texts
    for obj in content_object:
        if not isinstance(obj, dict):
            continue
        if "text" in obj and isinstance(obj["text"], str):
            texts.append(obj["text"])
            continue
        if "content" in obj and isinstance(obj["content"], list):
            for sub in obj["content"]:
                if isinstance(sub, dict) and isinstance(sub.get("text"), str):
                    texts.append(sub["text"])
    return [t.strip() for t in texts if t and t.strip()]


def normalize_text_for_hash(text: str) -> str:
    text = re.sub(r"\s+", "", text)
    # 去掉常见的中文引号差异
    text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")
    return text


def make_item_key(title: str, content_text: str) -> str:
    s = f"{title}||{normalize_text_for_hash(content_text)}"
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def score_text_length(content_type: str, n_chars: int) -> Tuple[int, List[str]]:
    """
    按类型做简单篇幅检查（面向“在家晨读”）。
    返回：扣分、标签
    """
    issues: List[str] = []
    penalty = 0

    if content_type in SHORT_TYPES:
        if n_chars < 8:
            penalty += 8
            issues.append("内容过短")
        elif n_chars < 14:
            penalty += 3
            issues.append("内容偏短")
        return penalty, issues

    # 非短类型
    if n_chars < 25:
        penalty += 15
        issues.append("内容过短")
    elif n_chars < 45:
        penalty += 8
        issues.append("内容偏短")
    elif n_chars > 450:
        penalty += 5
        issues.append("内容偏长")
    return penalty, issues


def score_task_quality(task: str) -> Tuple[int, List[str]]:
    issues: List[str] = []
    penalty = 0
    t = task.strip()
    if not t:
        return 0, issues

    if len(t) < 6:
        penalty += 6
        issues.append("任务过短")
    if len(t) > 120:
        penalty += 4
        issues.append("任务过长")

    # 可操作性：有没有明确指令/问句提示
    if not any(k in t for k in ["？", "?", "请", "用", "找", "圈", "写", "说", "想一想", "试着"]):
        penalty += 4
        issues.append("任务指令不够明确")

    return penalty, issues


def score_answer_quality(answer: str) -> Tuple[int, List[str]]:
    issues: List[str] = []
    penalty = 0
    a = answer.strip()
    if not a:
        return 0, issues
    if len(a) < 4:
        penalty += 6
        issues.append("答案过短")
    if len(a) > 220:
        # 太长不一定是坏事，但家庭晨读中可能不利于孩子自检
        penalty += 2
        issues.append("答案偏长")
    return penalty, issues


def infer_answer_field(item: Dict[str, Any]) -> str:
    # 你这批数据里常见：best_answer（多数文章）、taskAnswer（日积月累/应用类）
    for k in ["best_answer", "taskAnswer", "task_answer", "answer"]:
        v = item.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def has_translation(item: Dict[str, Any]) -> bool:
    v = item.get("translation")
    return isinstance(v, str) and v.strip() != ""


def evaluate_item(
    *,
    unit: int,
    file_name: str,
    week: int,
    day: int,
    theme: str,
    block_index: int,
    item: Dict[str, Any],
    duplicate_count: int,
) -> Tuple[int, List[str], Dict[str, Any]]:
    """
    返回：score, issues, row(dict for tsv)
    """
    issues: List[str] = []
    score = 100

    title = _safe_str(item.get("title"))
    content_type = _safe_str(item.get("type"))
    author = _safe_str(item.get("author"))
    dynasty = _safe_str(item.get("dynasty"))

    content_texts = extract_texts_from_content_object(item.get("contentObject"))
    content_text = "".join(content_texts)
    n_chars = len(re.sub(r"\s+", "", content_text))

    annotation = _safe_str(item.get("annotation"))
    task = _safe_str(item.get("task"))
    answer = infer_answer_field(item)

    # 基础字段完整性
    if not title:
        score -= 35
        issues.append("缺标题")
    if not content_type:
        score -= 25
        issues.append("缺type")
    if not content_texts:
        score -= 35
        issues.append("缺正文")

    # 作者/朝代
    if content_type != "daily_accumulation":
        if not author:
            score -= 6
            issues.append("缺作者")
    if content_type in {"ancient_poem", "classical_chinese", "classic_recitation"}:
        if not dynasty:
            score -= 4
            issues.append("缺朝代")

    # 注释 / 译文
    if content_type != "daily_accumulation":
        if not annotation:
            score -= 10
            issues.append("缺注释")
    if content_type in {"ancient_poem", "classical_chinese", "classic_recitation"}:
        if not has_translation(item):
            # 允许极少数不写译文，但在“在家晨读”场景里会降低可用性
            score -= 8
            issues.append("缺译文")

    # 任务 / 答案
    if not task:
        score -= 18
        issues.append("缺任务")
    else:
        p, more = score_task_quality(task)
        score -= p
        issues.extend(more)

    if not answer:
        score -= 18
        issues.append("缺答案")
    else:
        p, more = score_answer_quality(answer)
        score -= p
        issues.extend(more)

    # 篇幅
    p, more = score_text_length(content_type, n_chars)
    score -= p
    issues.extend(more)

    # 疑似重复（同标题+正文哈希）
    if duplicate_count > 1:
        score -= 5
        issues.append(f"疑似重复({duplicate_count})")

    score = int(clamp(score, 0, 100))

    row = {
        "unit": unit,
        "file": file_name,
        "week": week,
        "day": day,
        "theme": theme,
        "block_index": block_index,
        "read_level": READ_LEVEL_BY_BLOCK_INDEX.get(block_index, ""),
        "type": content_type,
        "title": title,
        "author": author,
        "dynasty": dynasty,
        "text_chars": n_chars,
        "has_annotation": "1" if bool(annotation) else "0",
        "has_translation": "1" if has_translation(item) else "0",
        "has_task": "1" if bool(task) else "0",
        "has_answer": "1" if bool(answer) else "0",
        "score": score,
        "issues": ";".join(sorted(set(issues))),
    }
    return score, issues, row


def load_all_items() -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    返回：
    - flat_items: 每条包含 day 元信息 + item 本身 + block_index
    - dup_counts: item_key -> count
    """
    flat: List[Dict[str, Any]] = []
    key_counter: Counter[str] = Counter()

    for f in UNIT_FILES:
        # 文件名形如：3年级下册1单元.txt
        unit_match = re.search(r"下册(\d+)单元", f.name)
        unit = int(unit_match.group(1)) if unit_match else 0

        data = json.loads(f.read_text(encoding="utf-8"))
        for day_obj in data:
            week = int(day_obj.get("week", 0) or 0)
            day = int(day_obj.get("day", 0) or 0)
            theme = _safe_str(day_obj.get("theme"))
            content_list = day_obj.get("content") or []
            for idx, item in enumerate(content_list, start=1):
                if not isinstance(item, dict):
                    continue
                texts = extract_texts_from_content_object(item.get("contentObject"))
                content_text = "".join(texts)
                key = make_item_key(_safe_str(item.get("title")), content_text)
                key_counter[key] += 1
                flat.append(
                    {
                        "unit": unit,
                        "file": f.name,
                        "week": week,
                        "day": day,
                        "theme": theme,
                        "block_index": idx,
                        "item": item,
                        "item_key": key,
                    }
                )
    return flat, dict(key_counter)


def write_tsv(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "unit",
        "file",
        "week",
        "day",
        "theme",
        "block_index",
        "read_level",
        "type",
        "title",
        "author",
        "dynasty",
        "text_chars",
        "has_annotation",
        "has_translation",
        "has_task",
        "has_answer",
        "score",
        "issues",
    ]
    with path.open("w", encoding="utf-8") as f:
        f.write("\t".join(headers) + "\n")
        for r in rows:
            f.write("\t".join(_safe_str(r.get(h)).replace("\t", " ").replace("\n", " ") for h in headers) + "\n")


def write_md_report(
    *,
    rows: List[Dict[str, Any]],
    path: Path,
    issues_counter: Counter[str],
    avg_by_type: Dict[str, float],
    lowest_rows: List[Dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    avg_score = sum(int(r["score"]) for r in rows) / max(1, len(rows))
    with path.open("w", encoding="utf-8") as f:
        f.write("# 3年级下学期（无拼音）内容质量评估报告\n\n")
        f.write("## 概览\n\n")
        f.write(f"- 评估范围：3年级下册 1-8 单元，16周×6天，共 {len(rows)} 篇（按每个 content 条目计）\n")
        f.write(f"- 平均分：{avg_score:.2f}\n\n")

        f.write("## 问题标签统计（Top 20）\n\n")
        for k, v in issues_counter.most_common(20):
            f.write(f"- {k}: {v}\n")
        f.write("\n")

        f.write("## 各体裁平均分\n\n")
        for t, a in sorted(avg_by_type.items(), key=lambda x: (-x[1], x[0])):
            f.write(f"- {t}: {a:.2f}\n")
        f.write("\n")

        f.write("## 低分条目（Top 30，建议优先人工复核）\n\n")
        for r in lowest_rows:
            loc = f"第{r['week']}周第{r['day']}天"
            f.write(
                f"- 单元{r['unit']} | {loc} | 块{r['block_index']}({r['read_level']}) | {r['type']} | {r['title']} | 分数{r['score']} | {r['issues']}\n"
            )


def main() -> None:
    # 基本输入校验
    missing = [str(p) for p in UNIT_FILES if not p.exists()]
    if missing:
        raise SystemExit(f"缺少输入文件：{missing}")

    flat, dup_counts = load_all_items()

    rows: List[Dict[str, Any]] = []
    issues_counter: Counter[str] = Counter()
    scores_by_type: Dict[str, List[int]] = defaultdict(list)

    for obj in flat:
        score, issues, row = evaluate_item(
            unit=obj["unit"],
            file_name=obj["file"],
            week=obj["week"],
            day=obj["day"],
            theme=obj["theme"],
            block_index=obj["block_index"],
            item=obj["item"],
            duplicate_count=dup_counts.get(obj["item_key"], 1),
        )
        rows.append(row)
        if row["type"]:
            scores_by_type[row["type"]].append(score)
        for it in row["issues"].split(";"):
            if it.strip():
                issues_counter[it.strip()] += 1

    # 排序：按周/天/块
    rows.sort(key=lambda r: (int(r["unit"]), int(r["week"]), int(r["day"]), int(r["block_index"])))

    avg_by_type = {
        t: (sum(v) / len(v) if v else 0.0) for t, v in scores_by_type.items()
    }

    lowest_rows = sorted(rows, key=lambda r: int(r["score"]))[:30]

    write_tsv(rows, OUTPUT_TSV)
    write_md_report(
        rows=rows,
        path=OUTPUT_MD,
        issues_counter=issues_counter,
        avg_by_type=avg_by_type,
        lowest_rows=lowest_rows,
    )

    print(f"OK: wrote {OUTPUT_TSV}")
    print(f"OK: wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()

