#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 `内容/有拼音_重写版/<学期>/<年级>/*.txt`（JSON数组）导出为：
1) 公众号可用的 Markdown / 纯文本汇总
2) 文章汇总表（详细版）.txt（按你给的模板格式）

用法：
  python3 scripts/export_grade1_wechat_md.py --grade 1
  python3 scripts/export_grade1_wechat_md.py --grade 2
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ExportConfig:
    grade: int
    semester: str  # e.g. "下学期"

    @property
    def grade_dirname(self) -> str:
        return f"{self.grade}年级"

    @property
    def input_dir(self) -> Path:
        return REPO_ROOT / "内容" / "有拼音_重写版" / self.semester / self.grade_dirname

    @property
    def output_md_path(self) -> Path:
        return REPO_ROOT / "内容" / "有拼音_重写版" / f"{self.grade_dirname}_{self.semester}_公众号汇总.md"

    @property
    def output_txt_path(self) -> Path:
        return REPO_ROOT / "内容" / "有拼音_重写版" / f"{self.grade_dirname}_{self.semester}_公众号汇总.txt"

    @property
    def output_table_detailed_path(self) -> Path:
        return (
            REPO_ROOT
            / "汇总"
            / self.grade_dirname
            / f"文章汇总表（详细版）_有拼音_重写版_{self.semester}.txt"
        )


def _safe_str(v: Any) -> str:
    return "" if v is None else str(v)


def _has_text_pinyin_line(obj: Any) -> bool:
    return isinstance(obj, dict) and ("text" in obj) and ("pinyin" in obj)


def _render_text_pinyin_line(text: str, pinyin: str) -> str:
    text = text.strip()
    pinyin = pinyin.strip()
    if not text and not pinyin:
        return ""
    if text and pinyin:
        return f"{text}\n（{pinyin}）"
    return text or f"（{pinyin}）"


def _render_content_object(content_object: Any) -> str:
    """
    contentObject 可能是：
      - [{text,pinyin}, ...]
      - [{title,titlePinyin,content:[{text,pinyin}...]}]
    """
    if not isinstance(content_object, list) or not content_object:
        return ""

    # 形态 A：逐行 text/pinyin
    if all(_has_text_pinyin_line(x) for x in content_object):
        blocks: List[str] = []
        for line in content_object:
            blocks.append(
                _render_text_pinyin_line(
                    _safe_str(line.get("text")),
                    _safe_str(line.get("pinyin")),
                )
            )
        return "\n".join([b for b in blocks if b])

    # 形态 B：带 title 的列表（常见于“日积月累”）
    blocks2: List[str] = []
    for section in content_object:
        if not isinstance(section, dict):
            continue
        title = _safe_str(section.get("title")).strip()
        title_pinyin = _safe_str(section.get("titlePinyin")).strip()
        if title:
            blocks2.append(f"**{title}**" + (f"（{title_pinyin}）" if title_pinyin else ""))
        items = section.get("content")
        if isinstance(items, list) and items:
            for it in items:
                if not _has_text_pinyin_line(it):
                    continue
                t = _safe_str(it.get("text")).strip()
                p = _safe_str(it.get("pinyin")).strip()
                if t and p:
                    blocks2.append(f"- {t}（{p}）")
                elif t:
                    blocks2.append(f"- {t}")
                elif p:
                    blocks2.append(f"- （{p}）")
        blocks2.append("")  # section gap

    return "\n".join(blocks2).strip()


def _render_task(task: str, task_pinyin: str, answer: str, answer_pinyin: str) -> str:
    task = task.strip()
    task_pinyin = task_pinyin.strip()
    answer = answer.strip()
    answer_pinyin = answer_pinyin.strip()

    if not task and not answer:
        return ""

    parts: List[str] = []
    if task:
        parts.append("**小任务**")
        parts.append(_render_text_pinyin_line(task, task_pinyin) if task_pinyin else task)
    if answer:
        parts.append("**参考答案**")
        parts.append(_render_text_pinyin_line(answer, answer_pinyin) if answer_pinyin else answer)
    return "\n".join(parts)


@dataclass(frozen=True)
class DayItem:
    unit: int
    week: int
    day: int
    theme: str
    raw: dict

    @property
    def sort_key_date(self) -> Tuple[int, int]:
        return (self.week, self.day)

    @property
    def sort_key_unit(self) -> Tuple[int, int, int]:
        return (self.unit, self.week, self.day)


def _parse_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _load_all_items(cfg: ExportConfig) -> List[DayItem]:
    files = sorted(cfg.input_dir.glob(f"{cfg.grade_dirname}{'下册'}*单元.txt"))
    if not files:
        raise SystemExit(f"未找到输入文件：{cfg.input_dir}")

    items: List[DayItem] = []
    for fp in files:
        m = re.search(r"下册(\d+)单元", fp.name)
        unit = int(m.group(1)) if m else 0
        text = fp.read_text(encoding="utf-8").strip()
        data = json.loads(text)
        if not isinstance(data, list):
            continue
        for obj in data:
            if not isinstance(obj, dict):
                continue
            week = _parse_int(obj.get("week"), 0)
            day = _parse_int(obj.get("day"), 0)
            theme = _safe_str(obj.get("theme")).strip()
            if week <= 0 or day <= 0:
                continue
            items.append(DayItem(unit=unit, week=week, day=day, theme=theme, raw=obj))

    return items


def _render_one_day(item: DayItem) -> str:
    lines: List[str] = []
    lines.append(f"## 第{item.week}周 第{item.day}天｜{item.theme}")
    lines.append("")

    content = item.raw.get("content")
    if isinstance(content, list):
        for entry in content:
            if not isinstance(entry, dict):
                continue
            title = _safe_str(entry.get("title")).strip()
            title_pinyin = _safe_str(entry.get("titlePinyin")).strip()
            if title:
                lines.append(f"### {title}" + (f"（{title_pinyin}）" if title_pinyin else ""))
                lines.append("")

            body = _render_content_object(entry.get("contentObject"))
            if body:
                lines.append(body)
                lines.append("")

            task = _render_task(
                _safe_str(entry.get("task")),
                _safe_str(entry.get("taskPinyin")),
                _safe_str(entry.get("taskAnswer")),
                _safe_str(entry.get("taskAnswerPinyin")),
            )
            if task:
                lines.append(task)
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_one_day_txt(item: DayItem) -> str:
    lines: List[str] = []
    lines.append(f"【第{item.week}周 第{item.day}天】{item.theme}")
    lines.append("")

    content = item.raw.get("content")
    if isinstance(content, list):
        for entry in content:
            if not isinstance(entry, dict):
                continue
            title = _safe_str(entry.get("title")).strip()
            title_pinyin = _safe_str(entry.get("titlePinyin")).strip()
            if title:
                lines.append(f"《{title}》" + (f"（{title_pinyin}）" if title_pinyin else ""))
                lines.append("")

            body = _render_content_object(entry.get("contentObject"))
            if body:
                lines.append(body)
                lines.append("")

            task = _render_task(
                _safe_str(entry.get("task")),
                _safe_str(entry.get("taskPinyin")),
                _safe_str(entry.get("taskAnswer")),
                _safe_str(entry.get("taskAnswerPinyin")),
            )
            if task:
                # 去掉 markdown 粗体标记
                task_txt = (
                    task.replace("**小任务**", "【小任务】")
                    .replace("**参考答案**", "【参考答案】")
                )
                lines.append(task_txt)
                lines.append("")

    lines.append("=" * 24)
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _genre_zh(type_code: str) -> str:
    t = (type_code or "").strip()
    return {
        "children_poem": "童谣童诗",
        "modern_prose": "现代短文",
        "daily_accumulation": "日积月累",
        "ancient_poem": "古诗词",
        "riddle": "趣味谜语",
        "tongue_twister": "绕口令",
        # 项目里常见的更细分类
        "textbook_review": "课本复习",
        "story_legend": "故事传说",
        "classics": "国学经典",
        "classical_chinese": "小古文",
        # 兼容可能出现的其他命名
        "modern_text": "现代短文",
    }.get(t, t or "未知体裁")


def _daily_accumulation_subtitles(entry: dict) -> List[str]:
    """
    `daily_accumulation` 的 contentObject 里通常是若干子模块：
      [{"title":"四季词","titlePinyin":"...","content":[...]}, ...]
    这里提取子模块标题，用于“文章汇总表（详细版）”展示。
    """
    co = entry.get("contentObject")
    if not isinstance(co, list):
        return []
    titles: List[str] = []
    for sec in co:
        if not isinstance(sec, dict):
            continue
        t = _safe_str(sec.get("title")).strip()
        if t:
            titles.append(t)
    return titles


def _format_table_row(
    unit: str,
    week: str,
    day: str,
    theme: str,
    articles: List[str],
    max_articles: int,
) -> str:
    # 尽量对齐模板的“|”分隔样式（不强依赖等宽字体）
    a = articles + ["", "", "", ""]
    a1, a2, a3, a4 = a[0], a[1], a[2], a[3]

    parts: List[str] = [
        f"{unit:<6}",
        f"{week:<4}",
        f"{day:<4}",
        f"{theme:<26}",
    ]

    # 文章列：按全表最大列数输出（如果全表没有第4篇，就不显示第4列）
    if max_articles >= 1:
        parts.append(f"{a1:<34}")
    if max_articles >= 2:
        parts.append(f"{a2:<34}")
    if max_articles >= 3:
        parts.append(f"{a3:<34}")
    if max_articles >= 4:
        parts.append(f"{a4}")

    return " | ".join(parts).rstrip()


def _render_article_table_detailed(cfg: ExportConfig, items_by_unit: List[DayItem]) -> Tuple[str, int, int]:
    """
    输出与 `汇总/*年级/文章汇总表（详细版）.txt` 相同风格的“文章汇总表（详细版）”。
    """
    header_line = "=" * 200
    sep_line = "-" * 200
    title = f"{cfg.grade}年级8个单元完整文章汇总（详细版）（有拼音_重写版·{cfg.semester}）"

    lines: List[str] = []
    lines.append(header_line)
    lines.append(title)
    lines.append(header_line)
    lines.append("")

    # 先扫一遍，判断全表是否存在“第4篇”
    max_articles = 0
    for it in items_by_unit:
        c = it.raw.get("content")
        if not isinstance(c, list):
            continue
        cnt = 0
        for e in c:
            if isinstance(e, dict) and _safe_str(e.get("title")).strip():
                cnt += 1
        max_articles = max(max_articles, min(cnt, 4))
    max_articles = max(1, min(max_articles, 4))

    header_cols: List[str] = [
        "单元       ",
        "周      ",
        "天      ",
        "主题                        ",
        "文章1[体裁]                             ",
    ]
    if max_articles >= 2:
        header_cols.append("文章2[体裁]                             ")
    if max_articles >= 3:
        header_cols.append("文章3[体裁]                             ")
    if max_articles >= 4:
        header_cols.append("文章4[体裁]")
    lines.append(" | ".join(header_cols).rstrip())
    lines.append(sep_line)

    day_count = 0
    article_count = 0

    for it in items_by_unit:
        day_count += 1
        content = it.raw.get("content")
        articles: List[str] = []
        if isinstance(content, list):
            for entry in content:
                if not isinstance(entry, dict):
                    continue
                type_code = _safe_str(entry.get("type")).strip()
                title2 = _safe_str(entry.get("title")).strip()
                if not title2:
                    continue
                genre = _genre_zh(type_code)

                # 按你的要求：如果是“日积月累”，直接显示子模块标题
                if type_code == "daily_accumulation":
                    subs = _daily_accumulation_subtitles(entry)
                    if subs:
                        # 多个子模块时用“、”串起来
                        title2 = "、".join(subs)
                    # 需求 1：子标题后面的 [日积月累] 不显示
                    articles.append(title2)
                else:
                    articles.append(f"{title2}[{genre}]")

        article_count += len(articles)
        articles = articles[:4]

        lines.append(
            _format_table_row(
                unit=f"第{it.unit}单元" if it.unit > 0 else "",
                week=f"第{it.week}周",
                day=f"第{it.day}天",
                theme=it.theme,
                articles=articles,
                max_articles=max_articles,
            )
        )

    lines.append("")
    lines.append(f"总计：{day_count} 天，共 {article_count} 篇文章")
    return ("\n".join(lines).rstrip() + "\n", day_count, article_count)


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--grade", type=int, default=1, help="年级，如 1 或 2")
    p.add_argument("--semester", type=str, default="下学期", help="学期目录名，如 下学期/上学期")
    return p


def main() -> None:
    args = _build_arg_parser().parse_args()
    cfg = ExportConfig(grade=args.grade, semester=args.semester)

    items = _load_all_items(cfg)
    items_by_date = sorted(items, key=lambda x: x.sort_key_date)
    items_by_unit = sorted(items, key=lambda x: x.sort_key_unit)

    out: List[str] = []
    out_txt: List[str] = []

    out.append(f"# {cfg.grade}年级（{cfg.semester}）晨读内容汇总（有拼音·重写版）")
    out.append("")
    out.append("适用：公众号展示 / 家庭共读 / 课堂晨读")
    out.append("")
    out.append("## 目录（按周）")
    out.append("")

    out_txt.append(f"{cfg.grade}年级（{cfg.semester}）晨读内容汇总（有拼音·重写版）")
    out_txt.append("适用：公众号展示 / 家庭共读 / 课堂晨读")
    out_txt.append("")
    out_txt.append("目录（按周）")
    out_txt.append("")
    current_week: Optional[int] = None
    for it in items_by_date:
        if current_week != it.week:
            current_week = it.week
            out.append(f"- 第{it.week}周")
            out_txt.append(f"第{it.week}周")
        out.append(f"  - 第{it.week}周 第{it.day}天｜{it.theme}")
        out_txt.append(f"  - 第{it.week}周 第{it.day}天｜{it.theme}")
    out.append("")
    out.append("---")
    out.append("")

    out_txt.append("")
    out_txt.append("=" * 24)
    out_txt.append("")

    for it in items_by_date:
        out.append(_render_one_day(it))
        out_txt.append(_render_one_day_txt(it))

    cfg.output_md_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.output_md_path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    cfg.output_txt_path.write_text("\n".join(out_txt).rstrip() + "\n", encoding="utf-8")
    print(f"已生成：{cfg.output_md_path}")
    print(f"已生成：{cfg.output_txt_path}")

    # 文章汇总表（详细版）——对齐 `汇总/*年级/文章汇总表（详细版）.txt` 风格
    table_text, _, _ = _render_article_table_detailed(cfg, items_by_unit)
    cfg.output_table_detailed_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.output_table_detailed_path.write_text(table_text, encoding="utf-8")
    print(f"已生成：{cfg.output_table_detailed_path}")


if __name__ == "__main__":
    main()

