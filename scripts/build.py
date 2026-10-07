#!/usr/bin/env python3
"""Génère le site statique « Revue Pépites Audio & Vidéo » dans docs/.

Source de vérité : data/revues/AAAA-MM-JJ.json (un fichier = un billet).
Sorties : docs/index.html, docs/revues/AAAA-MM-JJ.html, docs/tags/*.html,
docs/feed.xml, docs/style.css, docs/.nojekyll et COVERED.md (à la racine).
Python 3, bibliothèque standard uniquement.
"""

from __future__ import annotations

import html
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVUES = ROOT / "data" / "revues"
DOCS = ROOT / "docs"
COVERED = ROOT / "COVERED.md"

SITE_TITLE = "Revue Pépites Audio & Vidéo"
SITE_DESC = (
    "Veille logiciels, solutions et add-ons audio & vidéo — montage, encodage, "
    "captation, sous-titres, DAW, plugins, IA. Open source d’abord, tous les 2 jours."
)
SITE_URL = "https://olanlive.github.io/revue-audio-video/"
REPO_URL = "https://github.com/olanlive/revue-audio-video"

PRICE_LABELS = {
    "open-source": "Open source",
    "gratuit": "Gratuit (non libre)",
    "freemium": "Freemium",
    "payant": "Payant",
}
REQUIRED_ITEM_KEYS = (
    "name", "url", "what", "why", "license", "price", "maturity", "news", "news_date",
)

CSS = """\
:root {
  --bg: #13110f;
  --surface: #1e1a17;
  --border: #3a3029;
  --text: #f1ebe4;
  --muted: #b3a597;
  --accent: #ff9f5a;
  --accent-hover: #ffc08f;
  --tag-bg: #2c241e;
  --tag-text: #f3cfae;
  --oss: #7bd88f;
  --free: #8cc8ff;
  --paid: #ff8a8a;
  --radius: 8px;
  --font: system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  --max: 760px;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; }
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); text-decoration: underline; }
.wrap { max-width: var(--max); margin: 0 auto; padding: 1.25rem 1.25rem 3rem; }
header.site { border-bottom: 1px solid var(--border); margin-bottom: 2rem; padding-bottom: 1.25rem; }
header.site h1 { margin: 0 0 .35rem; font-size: 1.6rem; letter-spacing: -.02em; }
header.site h1 a { color: var(--text); }
.tagline { color: var(--muted); margin: 0; font-size: .95rem; }
nav.crumbs { font-size: .85rem; color: var(--muted); margin-bottom: 1.5rem; }
nav.crumbs a { color: var(--muted); }
.meta { color: var(--muted); font-size: .9rem; }
h2.section { font-size: 1.25rem; margin: 0 0 1rem; }
.post-card, .pepite { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.1rem 1.25rem; margin-bottom: 1rem; }
.post-card h3 { margin: 0 0 .35rem; font-size: 1.15rem; }
.post-card h3 a { color: var(--text); }
.post-card ul { margin: .5rem 0 0; padding-left: 1.2rem; color: var(--muted); font-size: .92rem; }
.intro { font-size: 1rem; margin-bottom: 1.5rem; }
.pepite h2 { margin: 0 0 .4rem; font-size: 1.2rem; }
.pepite h2 a { color: var(--text); }
.pepite dl { margin: .6rem 0; display: grid; grid-template-columns: 9.5rem 1fr; gap: .35rem .8rem; font-size: .93rem; }
.pepite dt { color: var(--muted); }
.pepite dd { margin: 0; }
.pepite p { margin: .45rem 0; }
.badges { display: flex; flex-wrap: wrap; gap: .4rem; margin: .2rem 0 .5rem; }
.badge { font-size: .75rem; font-family: var(--mono); padding: .15rem .55rem; border-radius: 999px; border: 1px solid var(--border); }
.badge.open-source { color: var(--oss); border-color: var(--oss); }
.badge.gratuit, .badge.freemium { color: var(--free); border-color: var(--free); }
.badge.payant { color: var(--paid); border-color: var(--paid); }
.badge.cat { color: var(--muted); }
.tags { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .6rem; }
.tag { display: inline-block; background: var(--tag-bg); color: var(--tag-text); font-size: .75rem; font-family: var(--mono); padding: .2rem .55rem; border-radius: 999px; border: 1px solid var(--border); }
.tag:hover { color: var(--accent-hover); text-decoration: none; border-color: var(--accent); }
.tag-cloud { display: flex; flex-wrap: wrap; gap: .5rem; margin: 1rem 0 2rem; }
.sources { font-size: .88rem; color: var(--muted); }
.sources li { margin-bottom: .2rem; }
footer.site { margin-top: 3rem; padding-top: 1.25rem; border-top: 1px solid var(--border); color: var(--muted); font-size: .85rem; }
code { font-family: var(--mono); font-size: .9em; }
@media (max-width: 560px) { .pepite dl { grid-template-columns: 1fr; } .pepite dt { margin-top: .3rem; } }
"""

MONTHS = ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
          "août", "septembre", "octobre", "novembre", "décembre"]


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def fr_date(iso: str) -> str:
    dt = datetime.strptime(iso, "%Y-%m-%d")
    day = "1er" if dt.day == 1 else str(dt.day)
    return f"{day} {MONTHS[dt.month]} {dt.year}"


def slugify(s: str) -> str:
    s = s.lower()
    for a, b in (("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("ç", "c"), ("ô", "o"), ("û", "u"), ("î", "i")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def page(title: str, body: str, *, depth: int = 0, crumbs=None, description: str = SITE_DESC) -> str:
    prefix = "../" * depth
    crumb_html = ""
    if crumbs:
        parts = []
        for i, (label, href) in enumerate(crumbs):
            if href and i < len(crumbs) - 1:
                parts.append(f'<a href="{esc(href)}">{esc(label)}</a>')
            else:
                parts.append(f"<span>{esc(label)}</span>")
        crumb_html = '<nav class="crumbs" aria-label="Fil d’Ariane">' + " / ".join(parts) + "</nav>"
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="stylesheet" href="{prefix}style.css">
  <link rel="alternate" type="application/rss+xml" title="{esc(SITE_TITLE)}" href="{prefix}feed.xml">
</head>
<body>
  <div class="wrap">
    <header class="site">
      <h1><a href="{prefix}index.html">{esc(SITE_TITLE)}</a></h1>
      <p class="tagline">{esc(SITE_DESC)}</p>
    </header>
    {crumb_html}
    {body}
    <footer class="site">
      <p>Veille audio / vidéo · open source d’abord (gratuit ou payant signalé) · tous les 2 jours vers 9h (Europe/Paris)</p>
      <p><a href="{REPO_URL}">Code source sur GitHub</a> · <a href="{prefix}tags/index.html">Tous les tags</a> · <a href="{prefix}feed.xml">Flux RSS</a></p>
    </footer>
  </div>
</body>
</html>
"""


def tags_html(tags, base: str) -> str:
    if not tags:
        return ""
    return '<div class="tags">' + "".join(
        f'<a class="tag" href="{base}{esc(t)}.html">#{esc(t)}</a>' for t in tags) + "</div>"


def load_posts() -> list[dict]:
    posts = []
    for f in sorted(REVUES.glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        p.setdefault("date", f.stem)
        p["slug"] = f.stem
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(-[a-z0-9-]+)?", f.stem):
            raise SystemExit(f"Nom de fichier invalide : {f.name} (attendu AAAA-MM-JJ.json)")
        items = p.get("items", [])
        if not 1 <= len(items) <= 10:
            raise SystemExit(f"{f.name} : nombre de pépites inattendu ({len(items)})")
        for it in items:
            missing = [k for k in REQUIRED_ITEM_KEYS if not it.get(k)]
            if missing:
                raise SystemExit(f"{f.name} / {it.get('name')} : champs manquants {missing}")
            if it["price"] not in PRICE_LABELS:
                raise SystemExit(f"{f.name} / {it['name']} : price doit être {list(PRICE_LABELS)}")
        posts.append(p)
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


def pepite_html(it: dict, tags_base: str) -> str:
    cat = f'<span class="badge cat">{esc(it["category"])}</span>' if it.get("category") else ""
    title = esc(it["name"]) + (f' {esc(it["version"])}' if it.get("version") else "")
    news_link = f' — <a href="{esc(it["news_url"])}" rel="noopener">source</a>' if it.get("news_url") else ""
    return f"""
<article class="pepite" id="{esc(slugify(it['name']))}">
  <h2><a href="{esc(it['url'])}" rel="noopener">{title}</a></h2>
  <div class="badges"><span class="badge {esc(it['price'])}">{esc(PRICE_LABELS[it['price']])}</span>{cat}</div>
  <p><strong>C’est quoi :</strong> {esc(it['what'])}</p>
  <p><strong>Pourquoi pour toi :</strong> {esc(it['why'])}</p>
  <dl>
    <dt>Licence / prix</dt><dd>{esc(it['license'])}</dd>
    <dt>Maturité</dt><dd>{esc(it['maturity'])}</dd>
    <dt>L’actu ({esc(fr_date(it['news_date']))})</dt><dd>{esc(it['news'])}{news_link}</dd>
  </dl>
  {tags_html(it.get('tags', []), tags_base)}
</article>"""


def build() -> None:
    posts = load_posts()
    if DOCS.exists():
        shutil.rmtree(DOCS)
    (DOCS / "revues").mkdir(parents=True)
    (DOCS / "tags").mkdir(parents=True)
    (DOCS / "style.css").write_text(CSS, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    by_tag: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    for p in posts:
        for it in p["items"]:
            for t in it.get("tags", []):
                by_tag[t].append((p, it))

    # Billets
    for p in posts:
        items = "".join(pepite_html(it, "../tags/") for it in p["items"])
        sources = ""
        if p.get("sources"):
            sources = '<section class="sources"><h2 class="section">Sources</h2><ul>' + "".join(
                f'<li><a href="{esc(s["url"])}" rel="noopener">{esc(s["label"])}</a></li>' for s in p["sources"]
            ) + "</ul></section>"
        body = f"""
<article>
  <p class="meta"><time datetime="{esc(p['date'])}">{esc(fr_date(p['date']))}</time> · {len(p['items'])} pépites</p>
  <h2 class="section" style="font-size:1.5rem">{esc(p['title'])}</h2>
  <p class="intro">{esc(p.get('intro', ''))}</p>
  {items}
  {sources}
</article>"""
        (DOCS / "revues" / f"{p['slug']}.html").write_text(
            page(f"{p['title']} · {SITE_TITLE}", body, depth=1,
                 crumbs=[("Accueil", "../index.html"), (fr_date(p["date"]), "")],
                 description=p.get("intro", SITE_DESC)[:200]),
            encoding="utf-8")

    # Accueil
    cards = "".join(
        f"""
<article class="post-card">
  <p class="meta"><time datetime="{esc(p['date'])}">{esc(fr_date(p['date']))}</time> · {len(p['items'])} pépites</p>
  <h3><a href="revues/{esc(p['slug'])}.html">{esc(p['title'])}</a></h3>
  <ul>{''.join(f'<li>{esc(it["name"])}{(" " + esc(it["version"])) if it.get("version") else ""} — {esc(PRICE_LABELS[it["price"]])}</li>' for it in p['items'])}</ul>
</article>""" for p in posts)
    cloud = "".join(f'<a class="tag" href="tags/{esc(t)}.html">#{esc(t)}</a>' for t in sorted(by_tag))
    home = f"""
<section>
  <h2 class="section">Billets</h2>
  <p class="meta">{len(posts)} billet{'s' if len(posts) != 1 else ''}, du plus récent au plus ancien</p>
  {cards or '<p class="meta">Aucun billet pour le moment.</p>'}
</section>
<section>
  <h2 class="section">Tags</h2>
  <div class="tag-cloud">{cloud or '—'}</div>
</section>"""
    (DOCS / "index.html").write_text(page(SITE_TITLE, home), encoding="utf-8")

    # Tags
    for t, entries in sorted(by_tag.items()):
        lst = "".join(
            f'<li><a href="../revues/{esc(p["slug"])}.html#{esc(slugify(it["name"]))}">{esc(it["name"])}'
            f'{(" " + esc(it["version"])) if it.get("version") else ""}</a> '
            f'<span class="meta">— {esc(fr_date(p["date"]))}</span></li>' for p, it in entries)
        (DOCS / "tags" / f"{t}.html").write_text(
            page(f"#{t} · {SITE_TITLE}", f'<h2 class="section">Tag <code>#{esc(t)}</code></h2><ul>{lst}</ul>',
                 depth=1, crumbs=[("Accueil", "../index.html"), ("Tags", "index.html"), (f"#{t}", "")]),
            encoding="utf-8")
    idx = " ".join(f'<a class="tag" href="{esc(t)}.html">#{esc(t)}</a><span class="meta">({len(e)})</span>'
                   for t, e in sorted(by_tag.items()))
    (DOCS / "tags" / "index.html").write_text(
        page(f"Tags · {SITE_TITLE}", f'<h2 class="section">Tous les tags</h2><div class="tag-cloud">{idx or "—"}</div>',
             depth=1, crumbs=[("Accueil", "../index.html"), ("Tags", "")]), encoding="utf-8")

    # RSS
    rss_items = "".join(
        f"""
  <item>
    <title>{esc(p['title'])}</title>
    <link>{SITE_URL}revues/{esc(p['slug'])}.html</link>
    <guid>{SITE_URL}revues/{esc(p['slug'])}.html</guid>
    <pubDate>{datetime.strptime(p['date'], '%Y-%m-%d').strftime('%a, %d %b %Y 09:00:00 +0200')}</pubDate>
    <description>{esc(p.get('intro', ''))}</description>
  </item>""" for p in posts)
    (DOCS / "feed.xml").write_text(f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel>
  <title>{esc(SITE_TITLE)}</title>
  <link>{SITE_URL}</link>
  <description>{esc(SITE_DESC)}</description>
  <language>fr</language>{rss_items}
</channel></rss>
""", encoding="utf-8")

    # COVERED.md (anti-doublons pour les prochains passages)
    rows = []
    for p in posts:
        for it in p["items"]:
            rows.append(f"| {p['date']} | {it['name']} | {it.get('version', '')} | {PRICE_LABELS[it['price']]} | {it['url']} |")
    COVERED.write_text(
        "# Outils déjà couverts\n\n"
        "Fichier **généré** par `scripts/build.py` à partir de `data/revues/*.json` — ne pas éditer à la main.\n"
        "Avant chaque nouveau billet : ne reprendre un outil déjà listé que s’il y a une **nouvelle version majeure ou une actu forte**, "
        "et le signaler comme suivi (« déjà vu le … »).\n\n"
        "Hors périmètre (voir `olanlive/revue-oss-3d`) : 3D, VFX, compositing, rendu, modélisation, shaders, add-ons Blender non vidéo.\n\n"
        "| Billet | Outil | Version | Licence/prix | Lien |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n",
        encoding="utf-8")

    print(f"OK : {len(posts)} billet(s), {sum(len(p['items']) for p in posts)} pépite(s), {len(by_tag)} tag(s) → {DOCS}")


if __name__ == "__main__":
    build()
