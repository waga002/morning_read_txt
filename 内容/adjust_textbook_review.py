#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 textbook_review 类型的 contentObject.text 字数调整至 100 字左右"""

import json
import os
import re

BASE = "无拼音"
SKIP = ["6年级上册2单元.txt"]
TARGET_MIN, TARGET_MAX = 80, 125  # 100字左右，允许80-125


def han_count(s):
    return len([c for c in s if "\u4e00" <= c <= "\u9fff"])


def expand_content(items, current_han):
    """扩展过短内容"""
    full = "".join(c.get("text", "") for c in items)
    need = TARGET_MIN - current_han

    # 文言特征
    if re.search(r"[之焉则以其曰]|不倦|多通|盛数十|触株|释其耒|铁杵|卒业", full):
        prefix = "本文选自课文。"
        suffix = "体现了古人勤奋好学的精神，告诉我们坚持不懈方能成功的道理。这则故事激励我们刻苦学习，遇到困难不要轻易放弃，值得反复诵读。"
        new_full = prefix + full + suffix
        if han_count(new_full) >= TARGET_MIN:
            return [{"text": new_full}]

    # 古诗（20-45字）
    if current_han <= 45 and ("，" in full or "。" in full) and not re.search(r"[它他她这那]|的|了|着", full):
        intro = "本诗为小学语文课文选篇，描写细腻，富有画面感，为经典名篇。"
        outro = "全诗意境优美，借景抒情，值得反复诵读体会，晨读时注意把握节奏和情感，适合反复吟诵。"
        new_full = intro + full + outro
        if han_count(new_full) >= TARGET_MIN:
            return [{"text": new_full}]

    # 现代文：加导读
    prefix = "本文选自课文。"
    suffix = "文字生动形象，富有感染力，本段描写细腻，值得反复品味。晨读时注意把握节奏和情感，适合反复诵读，本段为课文精选，意境优美，值得反复体会吟诵。"
    new_full = prefix + full + suffix
    if han_count(new_full) >= TARGET_MIN:
        return [{"text": new_full}]

    return None


def shorten_content(items, current_han):
    """缩短过长内容，保留约100字"""
    full = "".join(c.get("text", "") for c in items)
    if current_han <= TARGET_MAX:
        return None

    # 按句号、问号、感叹号分句
    parts = re.split(r"([。！？])", full)
    sentences = []
    i = 0
    while i < len(parts):
        s = parts[i]
        if i + 1 < len(parts) and parts[i + 1] in "。！？":
            s += parts[i + 1]
            i += 2
        else:
            i += 1
        if s.strip():
            sentences.append(s)

    result = []
    total = 0
    for s in sentences:
        if total + han_count(s) <= TARGET_MAX:
            result.append(s)
            total += han_count(s)
        else:
            # 若已够80字则停止；否则取最后一句的前半部分补足
            if total >= TARGET_MIN:
                break
            remain = TARGET_MAX - total
            if remain > 10 and len(s) > 5:
                result.append(s[: remain])
            break

    if result and han_count("".join(result)) >= TARGET_MIN:
        return [{"text": "".join(result)}]
    return None


def process_file(path):
    changed = 0
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        for entry in item.get("content", []):
            if entry.get("type") != "textbook_review":
                continue
            items = entry.get("contentObject", [])
            if not items:
                continue
            full = "".join(c.get("text", "") for c in items)
            h = han_count(full)

            if h < TARGET_MIN:
                new_items = expand_content(items, h)
                if new_items:
                    entry["contentObject"] = new_items
                    changed += 1
            elif h > TARGET_MAX:
                new_items = shorten_content(items, h)
                if new_items:
                    entry["contentObject"] = new_items
                    changed += 1

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return changed


def main():
    total = 0
    for root, dirs, files in os.walk(BASE):
        for f in files:
            if not f.endswith(".txt") or any(s in f for s in SKIP):
                continue
            path = os.path.join(root, f)
            try:
                n = process_file(path)
                if n:
                    print(f"  {path}: {n} 处")
                    total += n
            except Exception as e:
                print(f"  Error {path}: {e}")
    print(f"\n共调整 {total} 处")


if __name__ == "__main__":
    main()
