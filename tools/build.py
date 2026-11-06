#!/usr/bin/env python3
"""Build the static site: python tools/build.py

Reads src/pages/*.html (a JSON meta comment, then the page body) and writes
finished pages to the repo root, plus sitemap.xml. Commit the output: the
deploy workflow uploads it as is.
"""
import hashlib
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "pages"
SITE = "https://www.optic5.com"
ORG_ID = SITE + "/#organization"
AREAS = ["Austin", "Round Rock", "Cedar Park", "Georgetown", "Pflugerville", "Leander",
         "Lakeway", "Bee Cave", "Dripping Springs", "Buda", "Kyle", "San Marcos"]


def asset(path):
    """Versioned URL, so browsers fetch a file again whenever it changes."""
    digest = hashlib.md5((ROOT / path).read_bytes()).hexdigest()[:8]
    return f"/{path}?v={digest}"


def load_pages():
    pages = []
    for file in sorted(SRC.glob("*.html")):
        text = file.read_text(encoding="utf-8")
        match = re.match(r"<!--(\{.*?\})-->\s*", text, re.S)
        if not match:
            raise SystemExit(f"{file.name}: missing JSON meta comment")
        meta = json.loads(match.group(1))
        meta["body"] = text[match.end():]
        meta["source"] = file.name
        pages.append(meta)
    return pages


def out_file(path):
    if path.endswith(".html"):
        return ROOT / path.lstrip("/")
    return ROOT / path.strip("/") / "index.html" if path != "/" else ROOT / "index.html"


def strip_tags(text):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text))).strip()


def organization():
    return {
        "@type": "ProfessionalService",
        "@id": ORG_ID,
        "name": "Optic5",
        "url": SITE + "/",
        "logo": SITE + "/img/apple-touch-icon.png",
        "image": SITE + "/img/og.jpg",
        "description": "AI setup, workflow automation, websites, hosting and IT consulting "
                       "for small businesses in Austin, Texas.",
        "email": "hello@optic5.com",
        "telephone": "+1-713-909-0177",
        "foundingDate": "2007",
        "address": {"@type": "PostalAddress", "addressLocality": "Austin",
                    "addressRegion": "TX", "addressCountry": "US"},
        "areaServed": [{"@type": "City", "name": f"{a}, TX"} for a in AREAS],
        "knowsAbout": ["Artificial intelligence", "Business process automation",
                       "Web design", "Web hosting", "IT consulting"],
    }


def structured_data(page):
    url = SITE + page["path"]
    graph = [organization()]
    if page["path"] != "/":
        crumbs = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"}]
        for name, link in page.get("parents", []):
            crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1,
                           "name": name, "item": SITE + link})
        crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1,
                       "name": page["crumb"], "item": url})
        graph.append({"@type": "BreadcrumbList", "itemListElement": crumbs})
    if page.get("service"):
        graph.append({"@type": "Service", "name": page["service"], "serviceType": page["service"],
                      "url": url, "description": page["description"],
                      "provider": {"@id": ORG_ID},
                      "areaServed": {"@type": "City", "name": "Austin, TX"}})
    if page.get("article"):
        graph.append({"@type": "Article", "headline": page["h1"], "description": page["description"],
                      "mainEntityOfPage": url, "image": SITE + "/img/og.jpg",
                      "datePublished": page["published"], "dateModified": page["modified"],
                      "author": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID}})
    faqs = re.findall(r"<details>\s*<summary>(.*?)</summary>\s*(.*?)\s*</details>", page["body"], re.S)
    if faqs:
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": strip_tags(q),
             "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}} for q, a in faqs]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)


def head(page, css):
    title = html.escape(page["title"], quote=True)
    desc = html.escape(page["description"], quote=True)
    url = SITE + page["path"]
    if page.get("noindex"):
        seo = '<meta name="robots" content="noindex">'
    else:
        kind = "article" if page.get("article") else "website"
        seo = f"""<link rel="canonical" href="{url}">
  <meta property="og:type" content="{kind}">
  <meta property="og:site_name" content="Optic5">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{SITE}/img/og.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Optic5: AI automation, websites and hosting in Austin, Texas">
  <meta property="og:locale" content="en_US">
  <meta name="twitter:card" content="summary_large_image">
  <script type="application/ld+json">
{structured_data(page)}
  </script>"""
    preload = ('<link rel="preload" as="image" href="/img/hero.webp" media="(min-width: 701px)" fetchpriority="high">\n  '
               '<link rel="preload" as="image" href="/img/hero-tall.webp" media="(max-width: 700px)" fetchpriority="high">\n  '
               if page["path"] == "/" else "")
    return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  {seo}
  <meta name="theme-color" content="#0a0a0b">
  <link rel="icon" href="/img/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
  <link rel="preload" href="/fonts/space-grotesk.woff2" as="font" type="font/woff2" crossorigin>
  {preload}<link rel="stylesheet" href="{css}">
</head>"""


HEADER = """<a class="skip" href="#main">Skip to content</a>

  <header class="site-header">
    <nav class="wrap nav" aria-label="Main">
      <a href="/" class="logo" aria-label="Optic5 home"><i aria-hidden="true"></i>Optic5</a>
      <button class="menu-toggle" aria-expanded="false" aria-controls="nav-links">Menu</button>
      <ul class="nav-links" id="nav-links">
        <li><a href="/#services">Services</a></li>
        <li><a href="/#industries">Industries</a></li>
        <li><a href="/guides/">Guides</a></li>
        <li><a href="/#austin">Austin</a></li>
        <li><a href="/#faq">FAQ</a></li>
        <li><a href="#contact" class="nav-cta">Get in touch</a></li>
      </ul>
    </nav>
  </header>"""

CONTACT = """<section class="contact" id="contact">
      <div class="wrap">
        <h2>Let&rsquo;s talk.</h2>
        <div class="contact-grid">
          <div>
            <p>Tell us a little about your business and what&rsquo;s slowing you down. A real person reads every message.</p>
            <ul class="contact-info">
              <li><a href="mailto:hello@optic5.com">hello@optic5.com</a></li>
              <li><a href="tel:+17139090177">(713) 909-0177</a></li>
              <li class="place">Austin, Texas</li>
            </ul>
          </div>
          <form class="contact-form" action="/contact.php" method="post" novalidate>
            <div class="field"><label for="name">Name</label><input id="name" name="name" autocomplete="name" required></div>
            <div class="field"><label for="business">Business</label><input id="business" name="business" autocomplete="organization"></div>
            <div class="field"><label for="email">Email</label><input id="email" name="email" type="email" autocomplete="email" required></div>
            <div class="field"><label for="phone">Phone</label><input id="phone" name="phone" type="tel" autocomplete="tel"></div>
            <div class="field full">
              <label for="interest">Interested in</label>
              <select id="interest" name="interest">
                <option>AI &amp; automation</option>
                <option>Business optimization</option>
                <option>A new website or redesign</option>
                <option>Hosting or moving my site</option>
                <option>Consulting</option>
                <option>Not sure yet</option>
              </select>
            </div>
            <div class="field full"><label for="message">What&rsquo;s taking up too much of your time?</label><textarea id="message" name="message" required></textarea></div>
            <div class="hp" aria-hidden="true"><label for="website">Leave blank</label><input id="website" name="website" tabindex="-1" autocomplete="off"></div>
            <div class="field full"><div><button type="submit" class="btn btn-primary">Send message</button></div></div>
            <p class="form-status" role="status" aria-live="polite"></p>
          </form>
        </div>
      </div>
    </section>"""

FOOTER = """<footer>
    <div class="wrap">
      <div class="foot-links">
        <div>
          <h2>Services</h2>
          <ul>
            <li><a href="/ai-automation-austin/">AI &amp; automation</a></li>
            <li><a href="/business-process-consulting-austin/">Business optimization</a></li>
            <li><a href="/web-design-austin/">Web design</a></li>
            <li><a href="/web-hosting-austin/">Web hosting</a></li>
            <li><a href="/it-consulting-austin/">IT consulting</a></li>
          </ul>
        </div>
        <div>
          <h2>Industries</h2>
          <ul>
            <li><a href="/ai-for-contractors-austin/">Contractors &amp; home services</a></li>
            <li><a href="/ai-for-professional-services-austin/">Law, accounting &amp; advisory firms</a></li>
            <li><a href="/ai-for-restaurants-retail-austin/">Restaurants &amp; retail</a></li>
          </ul>
        </div>
        <div>
          <h2>Guides</h2>
          <ul>
            <li><a href="/guides/where-to-start-with-ai/">Where to start with AI</a></li>
            <li><a href="/guides/texas-ai-rules-small-business/">Texas AI rules explained</a></li>
            <li><a href="/guides/small-business-ai-policy-template/">AI policy template</a></li>
            <li><a href="/guides/busywork-calculator/">Busywork calculator</a></li>
          </ul>
        </div>
        <div>
          <h2>Contact</h2>
          <ul>
            <li><a href="mailto:hello@optic5.com">hello@optic5.com</a></li>
            <li><a href="tel:+17139090177">(713) 909-0177</a></li>
            <li>Austin, Texas</li>
          </ul>
        </div>
      </div>
      <p class="foot-base">&copy; <span id="year">2026</span> Optic5, Austin, Texas. Websites, hosting and consulting since 2007.</p>
    </div>
  </footer>"""


def page_head(page):
    crumbs = ['<a href="/">Home</a>']
    crumbs += [f'<a href="{link}">{name}</a>' for name, link in page.get("parents", [])]
    crumbs.append(f'<span aria-current="page">{page["crumb"]}</span>')
    updated = ""
    if page.get("article"):
        updated = f'<p class="updated">Updated <time datetime="{page["modified"]}">{page["modified_label"]}</time></p>'
    return f"""<section class="page-head">
      <div class="wrap">
        <nav class="crumbs" aria-label="Breadcrumb">{' <span aria-hidden="true">/</span> '.join(crumbs)}</nav>
        <h1>{page["h1"]}</h1>
        <p class="lede">{page["lede"]}</p>
        {updated}
      </div>
    </section>"""


def render(page, css, js):
    if page.get("bare"):
        main = f'<main id="main">{page["body"]}</main>'
        footer = ""
    else:
        intro = "" if page["path"] == "/" else page_head(page)
        main = f'<main id="main">\n    {intro}\n{page["body"]}\n    {CONTACT}\n  </main>'
        footer = FOOTER
    return f"""{head(page, css)}
<body>
  {HEADER.replace('href="#contact"', 'href="/#contact"') if page.get("bare") else HEADER}

  {main}

  {footer}

  <script src="{js}" defer></script>
</body>
</html>
"""


def main():
    css, js = asset("css/styles.css"), asset("js/main.js")
    pages = load_pages()
    urls = []
    for page in pages:
        target = out_file(page["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="\n") as f:
            f.write(render(page, css, js))
        if not page.get("noindex"):
            urls.append((SITE + page["path"], page["modified"]))
    urls.sort(key=lambda u: (u[0] != SITE + "/", u[0]))
    entries = "\n".join(f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{d}</lastmod>\n  </url>" for u, d in urls)
    with (ROOT / "sitemap.xml").open("w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + entries + "\n</urlset>\n")
    print(f"Built {len(pages)} pages, {len(urls)} in sitemap")


if __name__ == "__main__":
    main()
