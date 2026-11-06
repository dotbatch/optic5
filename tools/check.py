#!/usr/bin/env python3
"""SEO and link checks on the built site: python tools/check.py"""
import json
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://www.optic5.com"
problems = []
pages = {}
for sitemap_url in re.findall(r"<loc>(.*?)</loc>", (ROOT / "sitemap.xml").read_text(encoding="utf-8")):
    path = sitemap_url.replace(SITE, "")
    file = ROOT / path.strip("/") / "index.html" if path != "/" else ROOT / "index.html"
    if not file.exists():
        problems.append(f"sitemap lists a missing page: {path}")
        continue
    pages[path] = file.read_text(encoding="utf-8")

titles, descriptions = Counter(), Counter()
inbound = Counter()
for path, text in pages.items():
    title = re.search(r"<title>(.*?)</title>", text, re.S).group(1)
    desc = re.search(r'<meta name="description" content="(.*?)"', text).group(1)
    plain_title = title.replace("&amp;", "&")
    plain_desc = desc.replace("&#x27;", "'").replace("&amp;", "&")
    titles[title] += 1
    descriptions[desc] += 1
    if len(plain_title) > 60:
        problems.append(f"{path}: title is {len(plain_title)} chars")
    if not 110 <= len(plain_desc) <= 160:
        problems.append(f"{path}: description is {len(plain_desc)} chars")
    if text.count("<h1") != 1:
        problems.append(f"{path}: has {text.count('<h1')} h1 tags")
    if f'<link rel="canonical" href="{SITE}{path}">' not in text:
        problems.append(f"{path}: canonical is wrong")
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
        json.loads(block)
    ids = re.findall(r'\sid="([^"]+)"', text)
    for name, count in Counter(ids).items():
        if count > 1:
            problems.append(f"{path}: duplicate id {name}")
    words = len(re.sub(r"<[^>]+>", " ", re.search(r'<main id="main">(.*?)<section class="contact"', text, re.S).group(1)).split())
    print(f"{words:5d} words  {len(plain_title):3d}/60 title  {len(plain_desc):3d}/160 desc  {path}")
    for link in set(re.findall(r'(?:href|src|srcset)="(/[^"#?]*)', text)):
        target = ROOT / link.strip("/")
        if link != "/" and not (target.is_file() or (target / "index.html").is_file()):
            problems.append(f"{path}: broken link {link}")
        if link in pages or link.endswith("/"):
            inbound[link] += 1
for path in pages:
    if path != "/" and inbound[path] == 0:
        problems.append(f"{path}: no page links to it")
for value, count in list(titles.items()) + list(descriptions.items()):
    if count > 1:
        problems.append(f"duplicate title or description: {value}")

print()
print("\n".join(problems) if problems else f"All checks passed on {len(pages)} pages")
sys.exit(1 if problems else 0)
