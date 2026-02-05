#!/usr/bin/env python3
"""检查晨读内容中过短的文章。运行：python3 check_short_content.py"""
import json
from pathlib import Path
from collections import defaultdict

CONTENT_DIR = Path(__file__).resolve().parent / "内容" / "无拼音"
MIN_CHARS = 100
SHORT_TYPES = {"daily_accumulation", "ancient_poem", "classic_recitation", "classics", "classical_chinese"}

def count_chars(content_obj):
    total = 0
    for item in (content_obj or []):
        if isinstance(item, dict) and "text" in item:
            total += len(item["text"])
        elif isinstance(item, dict) and "content" in item:
            for c in item["content"]:
                if isinstance(c, dict) and "text" in c:
                    total += len(c["text"])
    return total

def main():
    short = []
    for f in CONTENT_DIR.rglob("*.txt"):
        try:
            data = json.load(open(f, encoding="utf-8"))
        except: continue
        for w in (data if isinstance(data, list) else [data]):
            for b in w.get("content", []):
                t, c = b.get("type", ""), count_chars(b.get("contentObject", []))
                if t not in SHORT_TYPES and 0 < c < MIN_CHARS:
                    short.append({"title": b.get("title",""), "type": t, "chars": c, "grade": w.get("grade","?"), "week": w.get("week","?"), "day": w.get("day","?"), "file": str(f).split("无拼音/")[-1]})
    short.sort(key=lambda x: x["chars"])
    by_type = defaultdict(list)
    for i in short: by_type[i["type"]].append(i)
    focus = ["textbook_review", "modern_prose", "story_legend"]
    print(f"=== 过短文章（<{MIN_CHARS}字）共 {len(short)} 篇 ===\n")
    for t in focus:
        items = by_type.get(t, [])
        if items:
            print(f"【{t}】{len(items)}篇")
            for i in items[:20]: print(f"  {i['chars']}字 | {i['grade']}年级 第{i['week']}周{i['day']}天 | {i['title']} | {i['file']}")
            if len(items) > 20: print(f"  ... 还有{len(items)-20}篇")
            print()

if __name__ == "__main__": main()
