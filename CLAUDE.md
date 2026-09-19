# ZazzuList — instructions projet (lu au démarrage de chaque session)

> Lire ensuite `etat.md` (état + prochaines étapes). Références : `NOTES_API_SENSCRITIQUE.md` (API, ids, pièges),
> `HISTORIQUE.md` (versions, décisions, backlog d'idées). Le `README.md` est la doc publique du dépôt.

## Ce que c'est
Site statique **https://cybermax73.github.io/zazzulist/** : films et séries notés ≥ 6 sur SensCritique, disponibles
sur les plateformes de streaming choisies par l'utilisateur (8 possibles), avec lien direct, filtres, 👍/👎, vu/passer.
Propriétaire : Max (GitHub `cybermax73`). Public cible : Max + amis, partage par simple lien. **Zéro coût, zéro serveur.**

## Où sont les choses
- `docs/index.html` — TOUTE la page (HTML + CSS + JS vanilla, aucune dépendance, aucun build). Servie par GitHub Pages.
- `docs/data/<univers>_<idPlateforme>.json` — catalogue, un fichier par univers (`films`, `series`) et par plateforme ;
  `docs/data/manifest.json` — plateformes (id, nom, logo), date, compteurs. `docs/img/` — logos plateformes.
- `scripts/fetch_catalog.py` — génère `docs/data/` depuis l'API SensCritique (stdlib only, ~8 min pour tout).
- `.github/workflows/refresh.yml` — lance le script chaque nuit (04:15 UTC) et commite si changement.
- `tools/cdp_test.py` — pilote Edge headless (DevTools) pour tester la page sans navigateur visible. Voir « Tester ».
- `max-zazzulist.json` — export perso de Max (votes). **Gitignoré, ne jamais le publier.**
- Anciennes versions locales (serveur Python, hors dépôt) : `..\sc-streaming` (v1) et `..\zazzulist` (v2). Ne pas y toucher,
  ce sont des sauvegardes ; la version de référence est ce dépôt.

## Règles
- Données utilisateur (plateformes, votes, vus) = **localStorage du navigateur uniquement** (`zazzulist_user_v1`,
  `zazzulist_filters_v1_<univers>`, `universe`). Pas de compte, pas de backend. Export/import JSON via ⚙.
  Si le schéma change, incrémenter la clé (`_v2`) plutôt que de casser les données existantes.
- Le dépôt est **public** : jamais de donnée personnelle, de clé, d'email dedans.
- Ne pas ajouter de dépendance (ni npm, ni pip). Page = un seul fichier ; script = stdlib.
- SensCritique = API non officielle : garder un rythme poli (pause 0,3 s entre pages, une passe par nuit), mention
  « données SensCritique » dans le footer. Si l'API change, le site continue d'afficher le dernier catalogue commité.
- Max n'est pas développeur : expliquer en français simple, proposer avant d'ajouter de la complexité, et lui laisser
  les choix produit. Il aime les interfaces épurées (il a fait retirer plusieurs contrôles).
- Chaque évolution notable = nouvelle entrée dans `HISTORIQUE.md` + mise à jour de `etat.md`.

## Déployer
`git add -A && git commit && git push` sur `main` → Pages redéploie en ~1 min. `gh` est installé et connecté (`cybermax73`).
Vérifier : `curl -s https://cybermax73.github.io/zazzulist/data/manifest.json`. Lancer le robot à la main :
`gh workflow run refresh.yml --repo cybermax73/zazzulist` ; suivre : `gh run list --repo cybermax73/zazzulist`.

## Tester
1. `cd docs && python -m http.server 8080` (Ctrl+C pour arrêter ; sous Git Bash, `taskkill //F //IM python.exe`).
2. Écrire un fichier de lignes JS (une expression par ligne, `sleep N` pour attendre) et lancer
   `APP_PORT=8080 python tools/cdp_test.py mon_test.js` : chaque ligne est évaluée dans la page, le résultat s'affiche.
   Exemples utiles : `document.getElementById('count').textContent`, `localStorage.clear(); location.reload(); 'ok'`,
   `document.querySelector('#formats .chip[data-fmt="animation"]').click(); 'x'`.
3. Capture d'écran : `msedge --headless=new --screenshot=<chemin> --window-size=1400,700 http://127.0.0.1:8080/`.

## Pièges connus
- Pagination SC instable → le script chevauche les pages (pas 50/100) et fusionne deux tris (voir NOTES).
- `[hidden]` doit être `display:none !important` (les `display:flex` des labels l'écrasaient).
- Ne jamais partager un tableau entre `DEFAULTS` et l'état courant (bug « réinitialiser » de la v2) : `freshDefaults()`.
- Les fichiers de plateforme fetchés à des moments différents peuvent lister des `platforms` incomplètes ; la page fait
  l'union par titre au chargement.
