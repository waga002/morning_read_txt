#!/usr/bin/env python3
"""扩充少于50字的文章"""
import json
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent / "内容" / "无拼音"
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

# 需要扩充的内容： (file_pattern, title, type) -> new_content
EXPANSIONS = {
    ("3年级下册2单元", "陶罐和铁罐", "textbook_review"): [
        {"text": ""你敢碰我吗，陶罐子！"铁罐傲慢地问。"不敢，铁罐兄弟。"陶罐谦虚地回答。"},
        {"text": ""总有一天，我要把你碰成碎片！"铁罐恼怒了。陶罐却不再理会铁罐，它知道争辩没有用，不如做好自己。"}
    ],
    ("5年级上册8单元", "囊萤夜读", "story_legend"): [
        {"text": "胤恭勤不倦，博学多通。家贫不常得油，夏月则练囊盛数十萤火以照书，以夜继日焉。"}
    ],
}

def main():
    for f in CONTENT_DIR.rglob("*.txt"):
        fstr = str(f)
        if "3年级下册2单元" not in fstr and "5年级上册8单元" not in fstr:
            continue
        try:
            data = json.load(open(f, encoding="utf-8"))
        except: continue
        modified = False
        for w in (data if isinstance(data, list) else [data]):
            for b in w.get("content", []):
                key = (fstr.split("/")[-1].replace(".txt",""), b.get("title",""), b.get("type",""))
                for (pat, title, typ), new_content in EXPANSIONS.items():
                    if pat in fstr and b.get("title") == title and b.get("type") == typ:
                        b["contentObject"] = new_content
                        if "annotation" in b and "恭勤" not in b.get("annotation",""):
                            b["annotation"] = "恭勤：肃敬勤勉。！！练囊：白绢做的口袋。！！以夜继日：日夜不停。"
                        modified = True
                        print(f"Expanded: {fstr} | {title}")
        if modified:
            with open(f, "w", encoding="utf-8") as out:
                json.dump(data, out, ensure_ascii=False, indent=2)
    print("Done")

if __name__ == "__main__": main()
