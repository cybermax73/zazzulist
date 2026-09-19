# ZazzuList — Historique et backlog

## Versions (toutes du 19/09/2026)
| Version | Dossier | Ce que c'est |
|---|---|---|
| v1 « Ce soir » | `..\sc-streaming` (port 8765) | Serveur Python local, Netflix + Canal+, films puis séries, filtres, 👍/👎, profils. Sauvegarde. |
| v2 « ZazzuList » | `..\zazzulist` (port 8766) | v1 + logo, badge nouvelle saison, tri « Pour toi », interface épurée. Sauvegarde. |
| **v3 web** | `zazzulist-web` (ce dépôt) | Site statique GitHub Pages, 8 plateformes au choix, robot nocturne, données dans le navigateur. **Référence.** |

## Journal
- **Besoin initial** : « les notes SC sont fiables, mais je ne sais pas ce qui est dispo ce soir sur myCanal/Netflix ».
- Exploration : SC expose `streamingExplorer` avec notes + dispo (données JustWatch) → une seule source, pas de matching.
- Pagination SC instable découverte et contournée (chevauchement + union de tris).
- Genres SC trop fins (47) → 12 thèmes ; catégorie SC (`Spectacle`, `Documentaire`…) → formats, ce qui a réglé le
  problème des stand-ups classés « Comédie » et de l'animation surreprésentée.
- Origine par continent (premier pays de production).
- Séries ajoutées : univers séparé, durée par épisode, saisons datées via les épisodes.
- Épuration demandée par Max : sous-titre, votes min, nouvelle saison (case), tri, puce Films/Séries retirés.
- Partage : choix de l'option « site statique gratuit + données dans le navigateur » (vs fichier à télécharger, vs site
  avec comptes). Mise en ligne le soir même ; `gh` installé et authentifié sur le poste de Max.
- Ajout des logos et de 4 plateformes (Apple TV+, MAX, Paramount+, Arte) ; import des votes de Max réussi.
- Retours mobile de Max (Xiaomi) : filtres trop encombrants → panneau glissant depuis le bas ; logos qui débordent dans la
  fenêtre plateformes → logos seuls ; curseur de note difficile → pouce 26 px, zone 44 px, `touch-action:none`, boutons − / +.

- Liste « à voir » ajoutée (bouton + vue), rappel d'export, demande de stockage persistant.

- Sauvegarde cloud par code secret (Cloudflare Worker + D1, gratuit) : décision Max après analyse des cas de perte
  (effacement navigateur, navigation privée, navigateur intégré, purge Safari 7 j, changement d'appareil). Node.js +
  wrangler installés sur le poste.

- Fix ⚙ muet (helper `ago` manquant après l'ajout de la synchro) — leçon : capturer les erreurs JS dans les tests.

## Backlog d'idées (brainstorm du 19/09, non priorisé, rien d'engagé)
- Pioche : 3 titres au hasard dans la sélection, plein écran, « re-tirer ».
- Départs imminents (« quitte Netflix le 30/09 ») — dépend de `vodPlatforms.modalities.dateEnd`, à vérifier.
- Acteurs dans la recherche (`actors { name }` dispo dans l'API, non stocké pour alléger).
- Compteurs de puces relatifs à la sélection courante plutôt qu'au catalogue entier.
- Lien bande-annonce (`medias.videos`).
- Tri « Pour toi » réactivé + page « profil » (ce que tes votes disent de toi) ; import des notes d'un compte SC (auth
  Firebase) pour démarrer avec des centaines de votes.
- Complément JustWatch pour les ~20 % de titres Canal+ absents du référentiel SC.
- Note pondérée par le nombre de votes (moyenne bayésienne) pour éviter les 8,3 à 60 votes.
- Raccourcis clavier ; alerte quand un titre « à voir » quitte le catalogue.
- Compteur de visites (GoatCounter / Cloudflare Analytics, gratuits, sans cookies).
- Comptes + synchro si le projet devient sérieux.

## Ce qu'on a écarté
- Lecteur vidéo / deep-linking apps : les liens directs suffisent.
- Scraper Netflix / myCanal : fragile ; SC + JustWatch couvrent le besoin.
- Base de données : deux JSON suffisent à cette échelle.
- Artifact Claude comme hébergement : pas de rafraîchissement automatisable, compte claude.ai requis pour les amis.
