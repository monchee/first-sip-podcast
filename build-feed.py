#!/usr/bin/env python3
# build-feed.py — First Sip podcast RSS generator (v1, 2026-11-08)
# Reads episodes.json + episodes/*.mp3, emits feed.xml. Idempotent.
import json, os, subprocess, sys
from datetime import datetime, timezone
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
open(os.path.join(BASE, "feed.xml"), "w", encoding="utf-8").write(xml)
print(f"feed.xml written: {len(meta['episodes'])} episode entries, {len(items)} with files")
