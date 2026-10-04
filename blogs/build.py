#!/usr/bin/env python3
"""Build the Writing section: blogs/<slug>/<slug>.md -> blogs/<slug>/index.html, plus blogs/index.html.

Usage:  python3 blogs/build.py
To add a post: create blogs/<slug>/<slug>.md (first line "# Title"), put its images next to it,
and add an entry to POSTS below. Requires the `markdown` package (pip install markdown).
"""
import html
import math
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent

# Order here is the order on the index page and in "Next post" links.
POSTS = [
    {
        "slug": "smart-glasses-kinyarwanda-vision-to-speech",
        "context": "Digital Umuganda internship · 2026",
        "summary": "More than 158,000 Rwandans live with visual impairment, and almost no assistive tools speak Kinyarwanda. This post describes a three-model cascade (4-bit VLM, int8 NLLB-200, Kinyarwanda TTS) that turns a camera frame into speech, analyses where its 31–43 s latency goes, and sets out the research questions for running it on-device in 3D-printed smart glasses.",
        "tags": ["VLM", "NLLB-200", "Kinyarwanda TTS", "Quantization", "Edge AI"],
        "cover": "Screenshot_from_2026-04-16_12-37-23.png",
        "cover_alt": "3D model of the VisionTTS glasses frame",
        "project": ("VisionTTS", "../../index.html#project-visiontts"),
    },
    {
        "slug": "sign-to-speech-rwanda-deaf-community",
        "context": "Digital Umuganda internship · 2026",
        "summary": "About 70,000 Rwandans are deaf or speech-impaired, yet Kinyarwanda Sign Language has no public dataset or model. This post builds both: 36,373 self-collected hand-landmark samples, a position- and scale-invariant 42-feature representation, and a 1,180-parameter classifier quantized to 6.9 KB, with an honest look at why its ~98.5% validation accuracy is likely optimistic.",
        "tags": ["MediaPipe", "TensorFlow Lite", "TinyML", "Accessibility"],
        "cover": "cover.jpeg",
        "cover_alt": "Illustrated hand-sign alphabet chart",
        "cover_fit": "contain",
        "project": ("Kinyarwanda Sign Language Recognition", "../../index.html#project-ksl"),
    },
    {
        "slug": "shrinking-heartbeat-classifier-tiny-devices",
        "context": "Italy research internship · University of Parma · Erasmus+ · 2026",
        "summary": "On-device ECG classification keeps patient data local and works without internet. This post quantizes a 5,125-parameter classifier to a 9 KB INT8 model, tests it on 1,000 synthetic printed-strip images (92.7% accuracy, 17.8 ms per image on one CPU core), shows the network is under 0.2% of total latency, and uses a confidence threshold to hand uncertain beats to a clinician.",
        "tags": ["Quantization", "TensorFlow Lite", "ECG", "Edge AI"],
        "cover": "dicovering param city.jpeg",
        "cover_alt": "Discovering the city centre of Parma",
        "project": ("AI Research & Engineering — University of Parma", "../../index.html#exp-parma"),
    },
]

# Images that are taller than wide get a capped height so they don't swamp the column.
PORTRAIT = {"gloves-iot.jpg", "we won.jpeg", "travling to italy.jpeg", "dicovering param city.jpeg"}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700'
         '&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">')

SCRIPT = """<script>
  var header = document.getElementById('siteHeader');
  var bar = document.getElementById('progress');
  function onScroll(){
    header.classList.toggle('scrolled', window.scrollY > 8);
    if(bar){
      var h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (h > 0 ? Math.min(100, window.scrollY / h * 100) : 0) + '%';
    }
  }
  window.addEventListener('scroll', onScroll, { passive:true });
  onScroll();
  document.getElementById('year').textContent = '\\u00a9 ' + new Date().getFullYear();
</script>"""


def esc(s):
    return html.escape(s, quote=True)


def header(home, writing, progress=False):
    return f"""<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header" id="siteHeader">
  <div class="header-inner">
    <a href="{home}index.html" class="mark" aria-label="Home">MZ</a>
    <nav class="site-nav" aria-label="Primary">
      <a href="{home}index.html#work" class="nav-optional">Work</a>
      <a href="{writing}index.html" aria-current="page">Writing</a>
      <a href="{home}index.html#contact" class="nav-cta">Contact</a>
    </nav>
  </div>
  {'<div class="progress" id="progress" aria-hidden="true"></div>' if progress else ''}
</header>"""


FOOTER = """<footer class="site-footer">
  <div class="wrap footer-inner">
    <span>Mohamed Zakaria Mohamed Ahmed — Kigali, Rwanda</span>
    <span id="year"></span>
  </div>
</footer>"""


def page(title, description, css, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{FONTS}
<link rel="stylesheet" href="{css}">
</head>
<body>
{body}
{SCRIPT}
</body>
</html>
"""


def read_post(post):
    src = (ROOT / post["slug"] / f"{post['slug']}.md").read_text(encoding="utf-8")
    first, _, rest = src.lstrip().partition("\n")
    post["title"] = first.lstrip("# ").strip()
    words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", rest)))
    post["minutes"] = max(1, math.ceil(words / 220))
    return rest


def figure(src, alt, caption):
    cls = ' class="portrait"' if html.unescape(src).replace("%20", " ") in PORTRAIT else ""
    return (f'<figure{cls}><img src="{src}" alt="{alt}" loading="lazy">'
            f'<figcaption>{caption}</figcaption></figure>')


def render(md_text):
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])
    body = md.convert(md_text)

    # Drop horizontal rules at the very start (the "---" right under the title).
    body = re.sub(r"^\s*(<hr\s*/?>\s*)+", "", body)
    # Collapse runs of rules left by blank sections.
    body = re.sub(r"(<hr\s*/?>\s*){2,}", "<hr>\n", body)

    # Markdown image followed by an italic caption -> <figure>
    img = r'<img alt="([^"]*)" src="([^"]+)"\s*/?>'
    body = re.sub(r"<p>" + img + r"\s*<em>(.*?)</em></p>",
                  lambda m: figure(m[2], m[1], m[3]), body, flags=re.S)
    body = re.sub(r"<p>" + img + r"</p>\s*<p><em>(.*?)</em></p>",
                  lambda m: figure(m[2], m[1], m[3]), body, flags=re.S)
    body = re.sub(r"<p>" + img + r"</p>", lambda m: figure(m[2], m[1], ""), body)

    # Responsive tables and video embeds
    body = body.replace("<table>", '<div class="table-scroll"><table>').replace("</table>", "</table></div>")
    body = re.sub(r"<iframe([^>]*)></iframe>",
                  lambda m: '<div class="video-embed"><iframe'
                            + re.sub(r'\s(width|height|frameborder)="[^"]*"', "", m[1])
                            + ' loading="lazy"></iframe></div>', body)

    # Lazy-load images in raw HTML figures too
    body = re.sub(r"<img (?![^>]*loading=)", '<img loading="lazy" ', body)

    toc = [(t["id"], t["name"]) for t in md.toc_tokens if t["level"] == 2]
    return body, toc


def meta_line(post):
    return (f'<p class="post-meta"><span class="ctx">{esc(post["context"])}</span>'
            f'<span>{post["minutes"]} min read</span></p>')


def build_post(post, next_post):
    body, toc = render(post["md"])
    toc_html = ""
    if len(toc) > 2:
        items = "\n".join(f'      <li><a href="#{i}">{n}</a></li>' for i, n in toc)
        toc_html = f"""<details class="toc">
    <summary>On this page · {len(toc)} sections</summary>
    <ol>
{items}
    </ol>
  </details>"""
    tags = "".join(f'<span class="tech-tag">{esc(t)}</span>' for t in post["tags"])
    proj_name, proj_href = post["project"]
    content = f"""{header("../../", "../", progress=True)}

<main id="main" class="article">
  <a class="back-link" href="../index.html">← All writing</a>
  <header class="article-head">
    {meta_line(post)}
    <h1>{esc(post["title"])}</h1>
    <div class="article-tags">{tags}</div>
  </header>

  {toc_html}

  <article class="prose">
{body}
  </article>

  <footer class="article-foot">
    <div class="related">
      <div><span>Related project</span><strong>{esc(proj_name)}</strong></div>
      <a class="read-link" href="{proj_href}">View on portfolio →</a>
    </div>
    <a class="next-post" href="../{next_post["slug"]}/index.html">
      <span>Next post →</span>
      <strong>{esc(next_post["title"])}</strong>
    </a>
    <a class="to-top" href="#top">↑ Back to top</a>
  </footer>
</main>

{FOOTER}"""
    html_out = page(f'{post["title"]} — Mohamed Zakaria', post["summary"], "../blog.css",
                    '<div id="top"></div>\n' + content)
    (ROOT / post["slug"] / "index.html").write_text(html_out, encoding="utf-8")


def build_index():
    items = []
    for p in POSTS:
        href = f'{p["slug"]}/index.html'
        cover = f'{p["slug"]}/{p["cover"]}'.replace(" ", "%20")
        items.append(f"""    <li class="post-item">
      <a class="post-item-cover{' fit-contain' if p.get('cover_fit') == 'contain' else ''}" href="{href}" tabindex="-1" aria-hidden="true"><img src="{cover}" alt="{esc(p["cover_alt"])}" loading="lazy"></a>
      <div class="post-item-body">
        {meta_line(p)}
        <h2><a href="{href}">{esc(p["title"])}</a></h2>
        <a class="read-link" href="{href}">Read the post →</a>
      </div>
    </li>""")
    content = f"""{header("../", "")}

<main id="main" class="wrap">
  <section class="page-head">
    <p class="eyebrow">Writing</p>
    <h1>Notes from the build</h1>
    <p class="page-lede">Long-form write-ups of the projects behind the portfolio: what I built, how it works, what the numbers really say, and what comes next.</p>
  </section>
  <ul class="post-list">
{chr(10).join(items)}
  </ul>
</main>

{FOOTER}"""
    out = page("Writing — Mohamed Zakaria",
               "Long-form write-ups by Mohamed Zakaria on edge AI, quantization and Kinyarwanda language technology.",
               "blog.css", content)
    (ROOT / "index.html").write_text(out, encoding="utf-8")


if __name__ == "__main__":
    for p in POSTS:
        p["md"] = read_post(p)
    for i, p in enumerate(POSTS):
        build_post(p, POSTS[(i + 1) % len(POSTS)])
        print(f"built {p['slug']}/index.html  ({p['minutes']} min)")
    build_index()
    print("built index.html")
