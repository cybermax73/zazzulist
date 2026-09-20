# ZazzuList

Les films et séries **bien notés sur SensCritique** (≥ 6/10) qui sont **disponibles ce soir** sur tes plateformes
(Netflix, Canal+, Prime Video, Disney+, Apple TV+, MAX, Paramount+, Arte), avec lien direct vers la plateforme.

Site statique : aucune inscription, aucun serveur. Tes 👍/👎, ta liste à voir et tes plateformes restent dans ton navigateur
(exportables / importables via ⚙ pour passer d'un appareil à l'autre).

## Comment ça marche

- `docs/index.html` — la page (HTML/JS sans dépendance), servie par GitHub Pages.
- `docs/data/<univers>_<plateforme>.json` — le catalogue, un fichier par plateforme ; la page ne charge que ceux
  de tes plateformes. `manifest.json` liste les plateformes et la date de mise à jour.
- `scripts/fetch_catalog.py` — interroge l'API publique de SensCritique (`streamingExplorer`) et écrit ces fichiers.
- `.github/workflows/refresh.yml` — lance le script chaque nuit et publie les données si elles ont changé.

## Faire tourner en local

    python scripts/fetch_catalog.py            # ~10 min, tout le catalogue
    python scripts/fetch_catalog.py films --providers 1,4
    cd docs && python -m http.server 8080       # puis http://localhost:8080

## Adapter

- Plateformes : `PROVIDERS` dans `scripts/fetch_catalog.py` (ids SensCritique ; Netflix 1, Canal+ 4, Prime 2, Disney+ 7,
  Apple TV+ 6, MAX 28, Arte 18, France TV 9, Paramount+ 19, TF1+ 27, M6+ 26…) et couleur `.plat.p<id>` dans `index.html`.
- Note minimale : `MIN_RATING`. Thèmes : `THEMES` dans `index.html`. Pays → continent : `CONTINENTS` dans le script.

Données : SensCritique (disponibilités JustWatch). Projet personnel, non affilié.
