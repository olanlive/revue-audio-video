#!/usr/bin/env python3
"""Build static HTML discovery feed for revue-audio-video into docs/ (+ COVERED.md).

Même logique que olanlive/revue-oss-3d : un fil plat de découvertes,
une page unique docs/index.html (plus récent en haut) + pages de tags.
"""

from __future__ import annotations

import html
import json
import re
import unicodedata
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "discoveries.json"
DOCS = ROOT / "docs"
TAGS_DIR = DOCS / "tags"
COVERED = ROOT / "COVERED.md"

SITE_TITLE = "Revue Pépites Audio & Vidéo"
SITE_DESC = "Veille logiciels, solutions et add-ons audio & vidéo — open source d’abord — tous les 2 jours."

CSS = """\
:root {
  --bg: #0f1419;
  --surface: #1a2332;
  --border: #2d3a4f;
  --text: #e7ecf3;
  --muted: #9aa8bc;
  --accent: #6cb6ff;
  --accent-hover: #9ad0ff;
  --tag-bg: #243044;
  --tag-text: #b8d4f0;
  --radius: 8px;
  --font: system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  --max: 720px;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  min-height: 100vh;
}
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); text-decoration: underline; }
.wrap {
  max-width: var(--max);
  margin: 0 auto;
  padding: 1.25rem 1.25rem 3rem;
}
header.site {
  border-bottom: 1px solid var(--border);
  margin-bottom: 2rem;
  padding-bottom: 1.25rem;
}
header.site h1 {
  margin: 0 0 0.35rem;
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}
header.site h1 a { color: var(--text); text-decoration: none; }
header.site h1 a:hover { color: var(--accent); }
.tagline { color: var(--muted); margin: 0; font-size: 0.95rem; }
nav.crumbs {
  font-size: 0.85rem;
  color: var(--muted);
  margin-bottom: 1.5rem;
}
nav.crumbs a { color: var(--muted); }
nav.crumbs a:hover { color: var(--accent); }
nav.crumbs span.sep { margin: 0 0.35rem; }
.meta { color: var(--muted); font-size: 0.9rem; }
.discovery {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.15rem 1.25rem;
  margin-bottom: 1rem;
}
.discovery h3 {
  margin: 0 0 0.5rem;
  font-size: 1.1rem;
}
.discovery h3 a { color: var(--text); }
.discovery h3 a:hover { color: var(--accent); }
.discovery .summary {
  margin: 0 0 0.75rem;
  color: var(--text);
  font-size: 0.95rem;
}
.discovery .source {
  margin: 0 0 0.75rem;
  color: var(--muted);
  font-size: 0.85rem;
}
.tags { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.tag {
  display: inline-block;
  background: var(--tag-bg);
  color: var(--tag-text);
  font-size: 0.75rem;
  font-family: var(--mono);
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  text-decoration: none;
}
.tag:hover {
  background: #2e4058;
  color: var(--accent-hover);
  text-decoration: none;
  border-color: var(--accent);
}
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 1rem 0 2rem;
  align-items: center;
}
h2.section {
  font-size: 1.25rem;
  margin: 0 0 1rem;
  font-weight: 600;
}
.date-label {
  color: var(--muted);
  font-size: 0.9rem;
  margin: 0 0 0.35rem;
}
footer.site {
  margin-top: 3rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.85rem;
}
.empty { color: var(--muted); }
code { font-family: var(--mono); font-size: 0.9em; }
@media (max-width: 520px) {
  .wrap { padding: 1rem 1rem 2.5rem; }
  header.site h1 { font-size: 1.35rem; }
}
"""


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def format_date_fr(iso: str) -> str:
    dt = datetime.strptime(iso, "%Y-%m-%d")
    months = [
        "", "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    ]
    return f"{dt.day} {months[dt.month]} {dt.year}"


def page(
    title: str,
    body: str,
    *,
    depth: int = 0,
    crumbs: list[tuple[str, str]] | None = None,
) -> str:
    """depth: 0 = docs/, 1 = docs/tags/."""
    prefix = "../" * depth
    crumb_html = ""
    if crumbs:
        parts = []
        for i, (label, href) in enumerate(crumbs):
            if i < len(crumbs) - 1 and href:
                parts.append(f'<a href="{esc(href)}">{esc(label)}</a>')
            else:
                parts.append(f"<span>{esc(label)}</span>")
        crumb_html = (
            '<nav class="crumbs" aria-label="Fil d’Ariane">'
            + '<span class="sep" aria-hidden="true"> / </span>'.join(parts)
            + "</nav>"
        )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(SITE_DESC)}">
  <link rel="stylesheet" href="{prefix}style.css">
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
      <p>Veille audio / vidéo · open source d’abord (gratuit / payant signalé) · tous les 2 jours · 9h Europe/Paris</p>
      <p><a href="https://github.com/olanlive/revue-audio-video">Code source sur GitHub</a>
         · <a href="{prefix}tags/index.html">Tous les tags</a></p>
    </footer>
  </div>
</body>
</html>
"""


def tags_html(tags: list[str], *, tags_base: str) -> str:
    if not tags:
        return ""
    links = [
        f'<a class="tag" href="{tags_base}{esc(t)}.html">#{esc(t)}</a>'
        for t in tags
    ]
    return '<div class="tags">' + "".join(links) + "</div>"


def source_html(source) -> str:
    """source: {"label": str, "url": str?} or a plain string."""
    if not source:
        return ""
    if isinstance(source, str):
        return f'<p class="source">Trouvé via : {esc(source)}</p>'
    label = esc(source.get("label", ""))
    url = source.get("url")
    if url:
        label = f'<a href="{esc(url)}" rel="noopener" target="_blank">{label}</a>'
    return f'<p class="source">Trouvé via : {label}</p>'


def anchor_id(item: dict) -> str:
    """Ancre stable : AAAA-MM-JJ-nom-version (ex. 2026-10-07-audacity-4-0-1)."""
    if item.get("id"):
        return item["id"]
    name = unicodedata.normalize("NFKD", item["name"]).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{item['date']}-{slug}"


def discovery_html(
    item: dict,
    *,
    tags_base: str,
    show_date: bool = True,
) -> str:
    date_bit = ""
    if show_date and item.get("date"):
        date_bit = (
            f'<p class="date-label"><time datetime="{esc(item["date"])}">'
            f"{esc(format_date_fr(item['date']))}</time></p>"
        )
    return f"""
<article class="discovery" id="{esc(anchor_id(item))}">
  {date_bit}
  <h3><a href="{esc(item['url'])}" rel="noopener" target="_blank">{esc(item['name'])}</a></h3>
  <p class="summary">{esc(item['summary'])}</p>
  {source_html(item.get('source'))}
  {tags_html(item.get('tags', []), tags_base=tags_base)}
</article>
"""


def build() -> None:
    discoveries = json.loads(DATA.read_text(encoding="utf-8"))
    discoveries = sorted(discoveries, key=lambda d: d["date"], reverse=True)

    if DOCS.exists():
        for child in DOCS.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    DOCS.mkdir(parents=True, exist_ok=True)
    TAGS_DIR.mkdir(parents=True, exist_ok=True)

    (DOCS / "style.css").write_text(CSS, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    by_tag: dict[str, list[dict]] = defaultdict(list)
    all_tags: set[str] = set()

    for item in discoveries:
        for tag in item.get("tags", []):
            all_tags.add(tag)
            by_tag[tag].append(item)

    feed = "".join(
        discovery_html(item, tags_base="tags/") for item in discoveries
    )
    tag_links = "".join(
        f'<a class="tag" href="tags/{esc(t)}.html">#{esc(t)}</a>'
        for t in sorted(all_tags)
    )
    n = len(discoveries)
    home_body = f"""
<section>
  <h2 class="section">Découvertes</h2>
  <p class="meta">{n} découverte{'s' if n != 1 else ''}</p>
  {feed if feed else '<p class="empty">Aucune découverte pour le moment.</p>'}
</section>
<section>
  <h2 class="section">Tags</h2>
  <div class="tag-cloud">{tag_links or '<span class="empty">—</span>'}</div>
</section>
"""
    (DOCS / "index.html").write_text(
        page(SITE_TITLE, home_body, depth=0), encoding="utf-8"
    )

    for tag in sorted(all_tags):
        entries = sorted(by_tag[tag], key=lambda e: e["date"], reverse=True)
        items_html = "".join(
            discovery_html(item, tags_base="./") for item in entries
        )
        body = f"""
<h2 class="section">Tag <code>#{esc(tag)}</code></h2>
<p class="meta">{len(entries)} découverte{'s' if len(entries) != 1 else ''}</p>
{items_html}
"""
        (TAGS_DIR / f"{tag}.html").write_text(
            page(
                f"#{tag} · {SITE_TITLE}",
                body,
                depth=1,
                crumbs=[
                    ("Accueil", "../index.html"),
                    ("Tags", "index.html"),
                    (f"#{tag}", ""),
                ],
            ),
            encoding="utf-8",
        )

    cloud_parts = []
    for t in sorted(all_tags):
        cloud_parts.append(
            f'<a class="tag" href="{esc(t)}.html">#{esc(t)}</a>'
            f'<span class="meta">({len(by_tag[t])})</span>'
        )
    tags_index_body = f"""
<h2 class="section">Tous les tags</h2>
<div class="tag-cloud">{' '.join(cloud_parts) or '<span class="empty">—</span>'}</div>
"""
    (TAGS_DIR / "index.html").write_text(
        page(
            f"Tags · {SITE_TITLE}",
            tags_index_body,
            depth=1,
            crumbs=[("Accueil", "../index.html"), ("Tags", "")],
        ),
        encoding="utf-8",
    )

    rows = "\n".join(
        f"| {d['date']} | {d['name']} | {', '.join(d.get('tags', []))} | {d['url']} | "
        f"https://olanlive.github.io/revue-audio-video/#{anchor_id(d)} |"
        for d in discoveries
    )
    COVERED.write_text(
        "# Outils déjà couverts\n\n"
        "Fichier **généré** par `scripts/build.py` depuis `data/discoveries.json` — ne pas éditer à la main.\n"
        "Avant d’ajouter une découverte : ne reprendre un outil déjà listé que s’il y a une nouvelle version "
        "majeure ou une actu forte (et le dire dans le résumé : « déjà vu le … »).\n\n"
        "Hors périmètre (voir `olanlive/revue-oss-3d`) : 3D, VFX, compositing, rendu, modélisation, shaders, "
        "add-ons Blender non vidéo.\n\n"
        "| Date | Découverte | Tags | Lien officiel | Ancre sur le site |\n|---|---|---|---|---|\n"
        + rows + "\n",
        encoding="utf-8",
    )

    print(f"Built {len(discoveries)} discovery(ies), {len(all_tags)} tag(s) → {DOCS}")


if __name__ == "__main__":
    build()
