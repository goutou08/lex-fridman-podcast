#!/usr/bin/env python3
"""
Lex Fridman TTS Podcast RSS Feed Generator
Generates an Apple Podcasts-compatible RSS feed from local MP3 files.

Usage:
    python generate_feed.py [--repo <github-pages-url>]
"""

import os
import re
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).parent
EPISODES_DIR = BASE_DIR / "episodes"
OUTPUT_FILE  = BASE_DIR / "feed.xml"

# Channel metadata
CHANNEL = {
    "title":       "Lex Fridman Podcast (中文精读版)",
    "link":        "https://lexfridman.com",
    "description": (
        "Lex Fridman 播客中文精读 TTS 版。"
        "由 AI 生成的中文语音，由 Hermes Agent 自动化制作。"
    ),
    "language":    "zh-CN",
    "author":      "Hermes Agent",
    "email":       "",
    "image_url":   "",
    "category":    "Technology",
    "explicit":    "false",
}

# Episode data: ep_number -> (title, guest, pub_date, category)
# Dates must be RFC 2822 compliant: "Mon, 01 Jan 2026 00:00:00 +0000"
EPISODE_DATA = {
    # Format: (title_part, guest, pub_date_rfc2822, category, duration_sec)
    495: (
        "Vikings, Ragnar, Berserkers, Valhalla & the Warriors of the Viking Age",
        "Lars Brownworth",
        "Mon, 23 Mar 2026 00:00:00 +0000",
        "History",
        638,
    ),
    494: (
        "NVIDIA – The $4 Trillion Company & the AI Revolution",
        "Jensen Huang",
        "Mon, 23 Mar 2026 00:00:00 +0000",
        "Technology",
        472,
    ),
    493: (
        "World of Warcraft, Overwatch, Blizzard, and Future of Gaming",
        "Jeff Kaplan",
        "Wed, 11 Mar 2026 00:00:00 +0000",
        "Gaming",
        889,   # 252+294+343
    ),
    492: (
        "Greatest Guitarists of All Time, History & Future of Music",
        "Rick Beato",
        "Tue, 04 Mar 2026 00:00:00 +0000",
        "Music",
        654,
    ),
    490: (
        "State of AI in 2026: LLMs, Coding, Scaling Laws, China, Agents, GPUs, AGI",
        "State of AI 2026",
        "Sun, 01 Feb 2026 00:00:00 +0000",
        "Technology",
        847,   # 382+465
    ),
    488: (
        "Infinity, Paradoxes that Broke Mathematics, Gödel Incompleteness & the Multiverse",
        "Joel David Hamkins",
        "Sun, 25 Jan 2026 00:00:00 +0000",
        "Mathematics",
        542,
    ),
    487: (
        "Deciphering Secrets of Ancient Civilizations & Flood Myths",
        "Irving Finkel",
        "Fri, 12 Dec 2025 00:00:00 +0000",
        "History",
        427,
    ),
    484: (
        "GTA, Red Dead Redemption, Rockstar, Absurd & Future of Gaming",
        "Dan Houser",
        "Fri, 31 Oct 2025 00:00:00 +0000",
        "Gaming",
        321,
    ),
    482: (
        "Telegram, Freedom, Censorship, Money, Power & Human Nature",
        "Pavel Durov",
        "Wed, 01 Oct 2025 00:00:00 +0000",
        "Technology",
        728,
    ),
    455: (
        "地外文明与宇宙中的生命",
        "Adam Frank",
        "Tue, 25 Nov 2025 00:00:00 +0000",
        "Science",
        571,
    ),
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_mp3_files():
    """Return sorted list of MP3 files (newest first by filename/episode number)."""
    files = sorted(EPISODES_DIR.glob("*.mp3"), key=lambda p: int(re.search(r'(\d+)', p.stem).group(1)), reverse=True)
    return files

def get_duration(file_path: Path) -> int:
    """Get MP3 duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(file_path)],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        return int(float(data["format"]["duration"]))
    except Exception:
        return 0

def format_duration(seconds: int) -> str:
    """Format seconds as HH:MM:SS for iTunes."""
    h, rem = divmod(seconds, 3600)
    m, s  = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"

def build_rfc2822(date_str: str) -> str:
    """Parse our date format and return RFC 2822 string."""
    dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

# ── RSS Builder ───────────────────────────────────────────────────────────────

def build_feed(base_url: str) -> str:
    """Build the complete RSS XML string."""

    items_xml = ""
    mp3_files = get_mp3_files()

    for mp3 in mp3_files:
        fname = mp3.name
        # Extract episode number from filename
        m = re.search(r'#?(\d+)', fname)
        if not m:
            continue
        ep_num = int(m.group(1))

        # Detect part suffix (e.g. part1, part2)
        part_m = re.search(r'-part(\d+)', fname, re.IGNORECASE)
        part_suffix = f" (第{part_m.group(1)}部分)" if part_m else ""

        # Get metadata
        if ep_num in EPISODE_DATA:
            title_part, guest, pub_rfc, category, stored_dur = EPISODE_DATA[ep_num]
            title = f"#{ep_num} — {guest}: {title_part}{part_suffix}"
            description = (
                f"Lex Fridman Podcast 第 {ep_num} 期。<br/>"
                f"嘉宾：{guest}。<br/>"
                f"由 Hermes Agent 生成的 AI 中文语音精读版。"
            )
            if part_suffix:
                description += f"<br/>{part_suffix}"
            pub_date = pub_rfc
            # Multi-part episodes: use actual per-file duration via ffprobe
            if part_m:
                actual_dur = get_duration(mp3)
                duration = format_duration(actual_dur) if actual_dur else format_duration(stored_dur)
            else:
                duration = format_duration(stored_dur)
        else:
            title     = fname.replace("_", " ").replace("#", "#")
            description = "Lex Fridman Podcast 精读版"
            pub_date   = "Mon, 01 Jan 2024 00:00:00 +0000"
            duration   = "0:00:00"

        # MP3 URL
        mp3_url = f"{base_url.rstrip('/')}/episodes/{fname}"

        # Get actual file size
        file_size = mp3.stat().st_size

        item = f"""    <item>
      <title>{escape(title)}</title>
      <description><![CDATA[{description}]]></description>
      <pubDate>{pub_date}</pubDate>
      <guid isPermaLink="false">{ep_num}{'-'+part_m.group(1) if part_m else ''}@lexfridman-tts</guid>
      <enclosure url="{mp3_url}" length="{file_size}" type="audio/mpeg" />
      <itunes:duration>{duration}</itunes:duration>
      <itunes:explicit>{CHANNEL['explicit']}</itunes:explicit>
      <itunes:author>{escape(guest if ep_num in EPISODE_DATA else 'Lex Fridman')}</itunes:author>
      <itunes:category text="{category if ep_num in EPISODE_DATA else 'Technology'}" />
    </item>"""
        items_xml += "\n" + item

    channel_img = ""
    if CHANNEL["image_url"]:
        channel_img = f'\n    <image>\n      <url>{CHANNEL["image_url"]}</url>\n      <title>{escape(CHANNEL["title"])}</title>\n      <link>{CHANNEL["link"]}</link>\n    </image>'

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
  xmlns:atom="http://www.w3.org/2005/Atom"
  xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{escape(CHANNEL['title'])}</title>
    <link>{CHANNEL['link']}</link>
    <description><![CDATA[{CHANNEL['description']}]]></description>{channel_img}
    <language>{CHANNEL['language']}</language>
    <itunes:author>{escape(CHANNEL['author'])}</itunes:author>
    <itunes:explicit>{CHANNEL['explicit']}</itunes:explicit>
    <itunes:category text="{CHANNEL['category']}" />
    <atom:link href="{base_url.rstrip('/')}/feed.xml" rel="self" type="application/rss+xml" />
{items_xml}
  </channel>
</rss>"""
    return rss

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Lex Fridman TTS Podcast RSS feed")
    parser.add_argument("--base-url", default="", help="Base URL for MP3 links, e.g. https://goutou08.github.io/lex-fridman-podcast")
    args = parser.parse_args()

    mp3_files = get_mp3_files()
    print(f"Found {len(mp3_files)} MP3 files:")
    for f in mp3_files:
        print(f"  {f.name}")

    rss_xml = build_feed(args.base_url)
    OUTPUT_FILE.write_text(rss_xml, encoding="utf-8")
    print(f"\nFeed written to: {OUTPUT_FILE}")
    print(f"Total episodes: {len(mp3_files)}")

if __name__ == "__main__":
    main()
