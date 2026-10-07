# Revue Pépites Audio & Vidéo

Repo : `revue-audio-video`

Veille **logiciels, solutions et add-ons audio & vidéo** pour un studio 3D : montage, encodage/transcodage (FFmpeg…), captation/streaming (OBS…), étalonnage, sous-titres, DAW, plugins audio, restauration/débruitage, outils IA audio/vidéo, add-ons vidéo/son pour Blender (VSE) ou autres.

Site statique (GitHub Pages) : **https://olanlive.github.io/revue-audio-video/**

Flux RSS 2.0 : **https://olanlive.github.io/revue-audio-video/feed.xml** (un item par découverte, lien vers l’ancre du bloc)

Cadence : **tous les 2 jours** vers **9h Europe/Paris** — 3 à 7 découvertes à chaque passage, ajoutées en tête d’un fil unique (même format que [`revue-oss-3d`](https://github.com/olanlive/revue-oss-3d)).

## Priorités

1. **Open source d’abord.** Gratuit non libre, freemium ou payant acceptés s’ils sont clairement signalés (tag + résumé).
2. **Résumé court et percutant : 1 à 2 phrases, ~280 caractères max** (le build avertit au-delà). Ce que fait l’outil ou ce qui est neuf dans cette version, avec la date de l’actu, pour donner envie de cliquer. Pas de pavé licence/maturité : la licence/le prix est porté par le **premier tag** ; une mention très courte (« bêta ») seulement si essentielle.
3. **Tout est vérifié sur les sources officielles** (site du projet, releases GitHub, changelog). Aucune version, date ou licence inventée.
4. **Hors périmètre** (couvert par `revue-oss-3d`) : 3D, VFX, compositing, rendu, modélisation, shaders, add-ons Blender non vidéo.
5. Pas de doublon : consulter [`COVERED.md`](./COVERED.md) avant d’ajouter.

## Ajouter une découverte

1. Éditer [`data/discoveries.json`](./data/discoveries.json) : ajouter un objet par découverte en tête (ou n’importe où — le build trie par date décroissante ; à date égale, l’ordre du fichier est conservé) :

```json
{
  "date": "2026-10-09",
  "name": "Nom de l’outil 1.2.3",
  "summary": "Ce que fait l’outil / ce qui est neuf (sortie le 8 oct). 1–2 phrases, ~280 caractères max.",
  "url": "https://site-officiel…",
  "tags": ["open-source", "montage", "ffmpeg"],
  "source": { "label": "Release GitHub — owner/repo 1.2.3", "url": "https://github.com/owner/repo/releases/tag/v1.2.3" }
}
```

- `date` = jour de publication (heure de Paris), format `AAAA-MM-JJ`.
- `name` = nom + version (la version fait partie de l’ancre).
- Le **premier tag** donne la licence/le prix : `open-source`, `gratuit`, `freemium` ou `payant`.
- `source` (optionnel) : où l’info a été vérifiée/repérée — affiché « Trouvé via : … ».

2. Rebuild (régénère `docs/` dont `docs/feed.xml`, et `COVERED.md`) :

```bash
python3 scripts/build.py
```

3. Commit + push `data/`, `docs/`, `COVERED.md` (et éventuellement ce README) :

```bash
git add data docs COVERED.md && git commit -m "Pépites AAAA-MM-JJ: Outil1 x.y, Outil2 x.y" && git push origin main
```

4. Lien vers une découverte : chaque bloc a une ancre stable `AAAA-MM-JJ-nom-version` (minuscules, accents retirés, tout caractère non alphanumérique → `-`), par ex. `https://olanlive.github.io/revue-audio-video/#2026-10-07-audacity-4-0-1`. Les ancres exactes sont listées dans `COVERED.md`.

## Tags (vocabulaire)

| Tag | Usage |
|-----|--------|
| `open-source` / `gratuit` / `freemium` / `payant` | Licence / prix (toujours en premier) |
| `montage` | Montage vidéo (NLE) |
| `encodage` | Encodage / transcodage / codecs |
| `ffmpeg` | Basé sur FFmpeg ou FFmpeg lui-même |
| `captation` / `streaming` | Capture, enregistrement, diffusion |
| `etalonnage` | Étalonnage / couleur vidéo |
| `sous-titres` | Sous-titrage, transcription |
| `audio` / `edition-audio` / `daw` / `plugin-audio` | Audio |
| `restauration` | Débruitage, restauration |
| `ia` | Outils IA audio/vidéo |
| `blender-addon` / `vse` | Add-ons Blender vidéo/son, Video Sequencer |
| `mlt` | Écosystème MLT (Shotcut, Kdenlive) |
| `gui` / `cli` | Interface graphique / ligne de commande |
| `securite` | Correctif de sécurité notable |
| `beta` | Version bêta / préversion |
| `multiplateforme` | Windows / macOS / Linux |

## Architecture

- `data/discoveries.json` — fil plat de découvertes (éditable)
- `scripts/build.py` — génère le HTML dans `docs/` et `COVERED.md`
- `docs/` — site publié (Pages depuis `main` / dossier `/docs`) : `index.html` (page unique, plus récent en haut), `tags/*.html`, `feed.xml` (RSS 2.0, 100 dernières découvertes)
- `COVERED.md` — liste générée des outils déjà couverts, avec ancres

Pas de npm. Python 3 standard library uniquement.

## Licence

Notes de veille (liens vers les projets upstream, chacun avec sa propre licence).
