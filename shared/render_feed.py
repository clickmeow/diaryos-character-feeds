from pathlib import Path
import csv, html

ROOT = Path(__file__).resolve().parents[1]
CHAR_DIR = ROOT / "characters"
PLATFORMS = [("public_feed","推搭大号（公开）"),("private_moments","微信朋友圈（老板可见）"),("private_alt","推搭小号（私密）")]

def read_rows(path):
    return list(csv.DictReader(path.open("r", encoding="utf-8-sig")))

def row_sort_key(row):
    phase_order = {"开局前历史": 0, "游戏开始后": 1, "发现小号后": 2}
    phase = phase_order.get(row.get("phase", ""), 9)
    timeline = row.get("timeline", "")
    if "月" in timeline:
        month, day = timeline.replace("日", "").split("月")
        order = int(month) * 100 + int(day)
    elif timeline.startswith("D"):
        order = 10000 + int(timeline[1:])
    elif timeline.startswith("小号"):
        order = 20000 + int(timeline[2:])
    else:
        order = 99999
    platform_order = {platform: index for index, (platform, _label) in enumerate(PLATFORMS)}
    return (phase, order, platform_order.get(row.get("platform", ""), 9), row.get("post_id", ""))

def group_rows(rows):
    grouped = {}
    ordered = []
    for row in sorted(rows, key=row_sort_key):
        key = (row.get("phase", ""), row.get("timeline", ""))
        if key not in grouped:
            grouped[key] = {"phase": key[0], "timeline": key[1], "event": row.get("event", ""), "cells": {p: [] for p, _label in PLATFORMS}}
            ordered.append(key)
        grouped[key]["cells"].setdefault(row.get("platform", ""), []).append(row)
    return grouped, ordered

def post_card(row):
    image = row.get("image_file", "")
    img = f'<img class="thumb" src="{html.escape(image)}" alt="{html.escape(row.get("post_id", ""))}">' if image else ""
    meta = []
    if row.get("unlock_condition"):
        meta.append("条件：" + row["unlock_condition"])
    if row.get("timestamp_mode"):
        meta.append("时间：" + row["timestamp_mode"])
    meta_html = f'<div class="meta">{html.escape(" / ".join(meta))}</div>' if meta else ""
    return '<div class="post"><div class="post-id">' + html.escape(row.get("post_id", "")) + '</div>' + img + '<div class="content">' + html.escape(row.get("content", "")) + '</div>' + meta_html + '</div>'

def render_character(character_dir):
    feed = character_dir / "feed.csv"
    if not feed.exists():
        return None
    rows = read_rows(feed)
    if not rows:
        return None
    name = rows[0].get("character_name") or character_dir.name
    grouped, ordered = group_rows(rows)
    trs = []
    for key in ordered:
        item = grouped[key]
        cells = []
        for platform, _label in PLATFORMS:
            cards = "".join(post_card(row) for row in item["cells"].get(platform, []))
            cells.append(f'<td class="platform-{platform}">{cards}</td>')
        trs.append('<tr><td class="stage">' + html.escape(item["phase"]) + '</td><td class="timeline">' + html.escape(item["timeline"]) + '</td><td class="event">' + html.escape(item["event"]) + '</td>' + ''.join(cells) + '</tr>')
    heads = ''.join('<th>' + html.escape(label) + '</th>' for _platform, label in PLATFORMS)
    doc = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>' + html.escape(name) + '动态时间流</title><link rel="stylesheet" href="../../shared/styles.css"></head><body><div class="header"><div><h1>' + html.escape(name) + '动态时间流</h1><div class="note">多平台角色动态档案。本页由 <code>feed.csv</code> 生成。</div></div><a href="../../index.html">返回角色入口</a></div><table class="feed-table"><thead><tr><th>阶段</th><th>时间</th><th>事件</th>' + heads + '</tr></thead><tbody>' + ''.join(trs) + '</tbody></table></body></html>'
    (character_dir / "index.html").write_text(doc, encoding="utf-8")
    return {"id": character_dir.name, "name": name, "count": len(rows), "href": "characters/" + character_dir.name + "/index.html"}

def render_index(characters):
    cards = ''.join('<a class="character-card" href="' + html.escape(char["href"]) + '"><strong>' + html.escape(char["name"]) + '</strong><span>' + html.escape(char["id"]) + ' · ' + str(char["count"]) + ' 条动态</span></a>' for char in characters)
    doc = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>DiaryOS Character Feeds</title><link rel="stylesheet" href="shared/styles.css"></head><body><div class="header"><div><h1>DiaryOS Character Feeds</h1><div class="note">角色多平台动态流展示仓库。适合给协作者或 AI 快速理解角色时间线。</div></div></div><div class="character-grid">' + cards + '</div></body></html>'
    (ROOT / "index.html").write_text(doc, encoding="utf-8")

def main():
    characters = []
    for character_dir in sorted(path for path in CHAR_DIR.iterdir() if path.is_dir()):
        rendered = render_character(character_dir)
        if rendered:
            characters.append(rendered)
    render_index(characters)
    print("rendered", len(characters), "characters")

if __name__ == "__main__":
    main()
