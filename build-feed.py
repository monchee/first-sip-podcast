#!/usr/bin/env python3
# build-feed.py — First Sip podcast RSS generator (v1, 2026-11-08)
# Reads episodes.json + episodes/*.mp3, emits feed.xml. Idempotent.
import json, os, subprocess, sys
from datetime import datetime, timezone
import html
from email.utils import format_datetime

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://podcast.monch.ee"
EP = os.path.join(BASE, "episodes")
meta = json.load(open(os.path.join(BASE, "episodes.json"), encoding="utf-8"))

def itunes_duration(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                              "-of", "csv=p=0", path], capture_output=True, text=True, timeout=20)
        secs = int(float(out.stdout.strip()))
        return f"{secs // 60}:{secs % 60:02d}"
    except Exception:
        return None

items = []
for ep in sorted(meta["episodes"], key=lambda e: e["date"], reverse=True):
    fname = ep["file"]
    path = os.path.join(EP, fname)
    if not os.path.exists(path):
        print(f"WARN: missing episode file {fname}", file=sys.stderr); continue
    size = os.path.getsize(path)
    url = f"{SITE}/episodes/{fname}"
    dur = itunes_duration(path)
    pub = datetime.strptime(ep["date"], "%Y-%m-%d").replace(hour=17, minute=15, tzinfo=timezone.utc)
    d = ep.get("description", "")
    items.append(f'''    <item>
      <title>{ep["title"]}</title>
      <description>{d}</description>
      <link>{SITE}/episodes/{ep["date"]}.html</link>
      <enclosure url="{url}" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{ep["date"]}-{fname}</guid>
      <pubDate>{format_datetime(pub)}</pubDate>
      <itunes:duration>{dur or "0:00"}</itunes:duration>
      <itunes:summary>{d}</itunes:summary>
    </item>''')

xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>The First Sip</title>
    <link>{SITE}</link>
    <language>en-au</language>
    <copyright>© {datetime.now().year} Monch</copyright>
    <description>Monch's morning brief, spoken by Rapi. Weather, training, world and AU news, and the extra shot: what's moving in AI today. Brewed daily in Sydney Olympic Park.</description>
    <itunes:author>Rapi for Monch</itunes:author>
    <itunes:summary>Monch's morning brief, spoken by Rapi. Weather, training, world and AU news, and the extra shot: what's moving in AI today. Brewed daily in Sydney Olympic Park.</itunes:summary>
    <itunes:type>episodic</itunes:type>
    <itunes:owner>
      <itunes:name>Monch</itunes:name>
      <itunes:email>me@monch.ee</itunes:email>
    </itunes:owner>
    <itunes:image href="{SITE}/art-3000.jpg"/>
    <itunes:category text="News"/>
    <itunes:explicit>false</itunes:explicit>
    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>
'''
# Shownotes pages: one HTML file per episode that has links
PAGE_TMPL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{date} \u2014 The First Sip</title>
<style>body{{font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;max-width:42rem;margin:2rem auto;padding:0 1.25rem;background:#fffaf2;color:#2b2118;line-height:1.55}}
h1{{font-size:1.4rem;margin:0 0 .2rem}} .date{{color:#a06a3a;margin:0 0 1.2rem;font-size:.9rem}}
h2{{font-size:1.02rem;margin:1.4rem 0 .4rem;color:#b3541e;text-transform:uppercase;letter-spacing:.04em;font-size:.82rem}}
li{{margin:.35rem 0}} a{{color:#b3541e}} .foot{{margin-top:2rem;font-size:.8rem;color:#9a8776}}</style></head>
<body><h1>The First Sip</h1><p class="date">{date} \u00b7 show notes</p>
{sections}
<p class="foot">Brewed daily in Sydney Olympic Park \u00b7 <a href="/">feed</a></p></body></html>"""
for ep in meta["episodes"]:
    links = ep.get("links") or []
    if not links: continue
    sections = {}
    for l in links:
        sections.setdefault(l.get("section", "Links"), []).append(l)
    blocks = []
    for sec, ls in sections.items():
        lis = "".join(f'<li><a href="{html.escape(x["url"], quote=True)}">{html.escape(x["title"])}</a></li>' for x in ls)
        blocks.append(f"<h2>{html.escape(sec)}</h2><ul>{lis}</ul>")
    page = PAGE_TMPL.format(date=ep["date"], sections="\n".join(blocks))
    outp = os.path.join(EP, ep["date"] + ".html")
    open(outp, "w", encoding="utf-8").write(page)
    print("page:", outp)

open(os.path.join(BASE, "feed.xml"), "w", encoding="utf-8").write(xml)
print(f"feed.xml written: {len(meta['episodes'])} episode entries, {len(items)} with files")
