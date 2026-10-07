# Revue Pépites Audio & Vidéo

Repo : `revue-audio-video`

Veille **logiciels, solutions et add-ons audio & vidéo** pour un studio 3D : montage, encodage/transcodage (FFmpeg…), captation/streaming (OBS…), étalonnage, sous-titres, DAW, plugins audio, restauration/débruitage, outils IA audio/vidéo, add-ons vidéo/son pour Blender (VSE) ou autres.

Site statique (GitHub Pages) : **https://olanlive.github.io/revue-audio-video/**

Cadence : **tous les 2 jours** vers **9h Europe/Paris** — un billet de 3 à 7 pépites.

## Ligne éditoriale

1. **Open source d’abord.** Gratuit non libre, freemium ou payant acceptés s’ils sont clairement signalés (champ `price`).
2. Chaque pépite : lien officiel, ce que c’est, pourquoi c’est utile au studio, licence/prix, maturité, et l’actu récente (avec date) qui la justifie.
3. **Tout est vérifié sur les sources officielles** (site du projet, releases GitHub, changelog). Aucune version, date ou licence inventée.
4. **Hors périmètre** (couvert par [`revue-oss-3d`](https://github.com/olanlive/revue-oss-3d)) : 3D, VFX, compositing, rendu, modélisation, shaders, add-ons Blender non vidéo.
5. Éviter les doublons : consulter [`COVERED.md`](./COVERED.md) avant chaque billet.

## Publier un nouveau billet

1. Créer `data/revues/AAAA-MM-JJ.json` (date du jour, heure de Paris) :

```json
{
  "date": "2026-10-09",
  "title": "Revue n°2 — …",
  "intro": "Deux ou trois phrases d’accroche.",
  "items": [
    {
      "name": "Nom de l’outil",
      "version": "1.2.3",
      "url": "https://site-officiel…",
      "category": "Montage vidéo",
      "what": "Ce que c’est.",
      "why": "Pourquoi c’est utile au studio.",
      "license": "Open source — GPL v3. Gratuit.",
      "price": "open-source",
      "maturity": "Mature / bêta / jeune projet…",
      "news": "Ce qui vient de sortir, avec la date.",
      "news_date": "2026-10-08",
      "news_url": "https://…/releases/tag/v1.2.3",
      "tags": ["montage", "ffmpeg"]
    }
  ],
  "sources": [{ "label": "Release GitHub 1.2.3", "url": "https://…" }]
}
```

`price` ∈ `open-source` | `gratuit` | `freemium` | `payant`. Champs obligatoires par pépite : `name`, `url`, `what`, `why`, `license`, `price`, `maturity`, `news`, `news_date` (le build échoue sinon).

2. Rebuild (régénère `docs/` et `COVERED.md`) :

```bash
python3 scripts/build.py
```

3. Commit + push :

```bash
git add data docs COVERED.md && git commit -m "Revue AAAA-MM-JJ : outil1, outil2, …" && git push origin main
```

4. Le billet est en ligne (après le build Pages, ~1 min) à :
`https://olanlive.github.io/revue-audio-video/revues/AAAA-MM-JJ.html`

## Tags (vocabulaire)

Tags kebab-case, en français : `montage`, `encodage`, `ffmpeg`, `captation`, `streaming`, `etalonnage`, `sous-titres`, `audio`, `edition-audio`, `daw`, `plugin-audio`, `restauration`, `ia`, `blender-addon`, `vse`, `mlt`, `gui`, `cli`, `securite`, `beta`, `multiplateforme`.

## Architecture

- `data/revues/AAAA-MM-JJ.json` — un fichier = un billet (source de vérité, éditable)
- `scripts/build.py` — génère le HTML dans `docs/` + `COVERED.md`
- `docs/` — site publié (GitHub Pages depuis `main` / dossier `/docs`) : `index.html` (billets du plus récent au plus ancien), `revues/*.html`, `tags/*.html`, `feed.xml` (RSS)
- `COVERED.md` — liste générée des outils déjà couverts (anti-doublons)

Pas de npm, pas de Jekyll (`docs/.nojekyll`). Python 3, bibliothèque standard uniquement.

## Licence

Notes de veille (liens vers les projets upstream, chacun avec sa propre licence).
