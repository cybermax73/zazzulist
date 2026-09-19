# ZazzuList — État (compact, source de vérité)

> Dernière mise à jour : **19/09/2026 (nuit)** — version mobile : filtres dans un panneau glissant. Lire `CLAUDE.md` d'abord.

## En prod
- **https://cybermax73.github.io/zazzulist/** — dépôt public `cybermax73/zazzulist`, Pages = branche `main`, dossier `/docs`.
- Robot nocturne GitHub Actions **vérifié** (1er passage 6 min, commit « Catalogue du 2026-09-19 »). Cron 04:15 UTC.
- Catalogue (≥ 6/10) : Netflix 1268 films / 1546 séries · Canal+ 255 / 162 · Prime Video 964 / 512 · Disney+ 710 / 366 ·
  MAX 362 / 266 · Paramount+ 278 / 88 · Arte 89 / 46 · Apple TV+ 40 / 107. 6,2 Mo sur disque, ~45 % transféré (gzip Pages).
- Max utilise Netflix + Canal+ ; ses 78 votes sont importés dans son navigateur (fichier `max-zazzulist.json`, copie dans
  `Téléchargements\ZazzuList-import-max.json`).

## Fonctionnalités de la page (docs/index.html)
- Toggle **Films / Séries** (univers séparés, filtres mémorisés par univers) ; sélecteur de plateforme parmi celles de
  l'utilisateur (masqué s'il n'en a qu'une) ; recherche titre/réalisateur.
- **Format** (tri-état inclure/exclure/neutre) : films = Animation, Documentaires, Spectacles (stand-up), Courts-métrages ;
  séries = Animation, Documentaires, Émissions & télé-réalité. Docs/spectacles/émissions/courts **exclus par défaut**.
- **Thèmes** (12, tri-état, mapping `THEMES`), **Origine** (6 continents, premier pays de production, table `CONTINENTS`
  dans le script), **Critères** : note ≥ (défaut 6,0), après <année>, durée max (séries : par épisode), vue
  (Tout / À voir / 👍 / 👎 / vus). Seuil de 100 votes appliqué en coulisses (contrôle masqué).
- Cartes : affiche, note SC colorée, votes, durée/saisons, genres, réalisateur/créateur, pays, synopsis dépliable,
  **logos plateformes cliquables** (lien direct), 👍/👎, ✓ vu / ✕ passer. Badges : NOUVEAU (arrivé < 7 j),
  Nouvelle saison / Nouvelle série (< 90 j), « S4 le 15 oct. » (à venir < 60 j).
- **Mobile (≤ 720 px)** : les filtres vivent dans un panneau qui glisse depuis le bas (bouton « Filtres » + badge du nombre
  de filtres actifs, bouton « Voir N films » pour fermer) ; le sélecteur de plateforme y est déplacé ; curseur de note
  agrandi + boutons − / + ; fenêtre plateformes = logos seuls.
- ⚙ : choix des plateformes (première visite = fenêtre obligatoire), export / import JSON, tout effacer.
- Code présent mais **masqué** (Max a voulu épurer) : tri « Pour toi » (affinité 👍/👎, `recoScore()`), tris popularité /
  année / nouveautés / aléatoire, sélecteur de votes min, case « nouvelle saison ».

## Décisions produit (Max)
- Une seule source : SensCritique (notes fiables, dispo JustWatch incluse). Pas de complément JustWatch pour l'instant.
- Pas de compte utilisateur, pas de serveur : données dans le navigateur. Réévaluer si beaucoup d'utilisateurs.
- Interface épurée : pas de sous-titre, pas de tri visible, pas de compteur de votes, aide tri-état à droite en discret.
- Plateformes retenues : les 8 ci-dessus (TF1+, M6+, France TV volontairement exclues).
- Garder les anciennes versions locales comme sauvegardes (`..\sc-streaming`, `..\zazzulist`).

## Prochaines étapes possibles (rien d'engagé)
1. Compteur de visites gratuit sans cookies (GoatCounter) — nécessite un compte à créer par Max ; snippet à ajouter
   dans `index.html`. Objectif : savoir si le site est utilisé avant d'investir plus.
2. Réactiver le tri « Pour toi » (ex. comme option du menu « Afficher ») quand Max le souhaitera ; il fonctionne dès 10 votes.
3. Liste « à voir » (wishlist) distincte de vu/passé ; raccourcis clavier ; bouton « pioche 3 titres au hasard ».
4. Date de fin de disponibilité (« quitte Netflix le … ») : champ `vodPlatforms.modalities.dateEnd` dans le schéma SC,
   **à vérifier s'il est peuplé**.
5. Si succès : comptes + synchro multi-appareils (Cloudflare/Supabase gratuit) — les données exportées sont déjà au bon format.
