# API SensCritique — ce qu'on sait (vérifié le 19/09/2026)

Tout a été découvert par essais (introspection désactivée) et en lisant le bundle JS de senscritique.com/films/streaming.
**Ne pas ré-explorer** : partir d'ici et de `scripts/fetch_catalog.py`.

## Endpoint
- `POST https://apollo.senscritique.com/` — GraphQL (Apollo Server), JSON `{query, variables}`.
- **Sans authentification.** Headers utilisés : `Content-Type: application/json`, `User-Agent` navigateur, `Origin`/`Referer`
  senscritique.com (par prudence).
- Une erreur GraphQL revient en HTTP 200 avec `errors[]` ; un enum invalide ou un champ inconnu → HTTP 400.

## Query principale : `streamingExplorer` (celle de la page « films en streaming »)
```graphql
query($providers:[Int], $rating:[Int], $subtype:String!, $limit:Int, $offset:Int, $order:StreamingSort) {
  streamingExplorer(providers:$providers, rating:$rating, subtype:$subtype, limit:$limit, offset:$offset, order:$order) {
    total
    products { id title originalTitle yearOfProduction dateRelease rating duration genres category synopsis url
               directors { name } creators { name } seasons { seasonNumber episodes { dateRelease } }
               countries { name } medias { picture } stats { ratingCount } providers { providerId name webUrl } }
  }
}
```
- `subtype` : `"movie"` ou `"tvShow"`. `rating` : `[min, max]` entiers (ex. `[6, 10]`). `limit` 100 accepté.
- Autres arguments existants (non utilisés) : `genres:[Int]`, `countries:[Int]`, `yearDateRelease:[Int,Int]`,
  `duration:[Int]`, `lastWeek`, `lastMonth`, `onlyPopular`, `seasons:[Int]`, `onlyWish`/`hideSeen` (compte requis).
- `order` — **seuls valides** : `RATING_DESC`, `POPULARITY_DESC`, `DATE_RELEASE_DESC`. Tout le reste → 400.

## Ids de plateformes (ids SensCritique, ≠ ids JustWatch)
Netflix 1 · Prime Video 2 · OCS 3 · Canal+ 4 · Apple TV+ 6 · Disney+ 7 · France TV 9 · Madelen 10 · Arte 18 ·
Paramount+ 19 · MUBI 20 · LaCinetek 21 · ADN 22 · Crunchyroll 23 · M6+ 26 · TF1+ 27 · MAX 28 · Shadowz 31 · Sooner 32.
Logos servis par SC : `https://www.senscritique.com/providersStreaming/<netflix|canalplus|primevideo|disneyplus|appletvplus|max|paramountplus|arte|francetv|ocs>.png` (450×120, copiés dans `docs/img/`).

## Pièges
- **Pagination instable** : les ex-æquo changent de page d'une requête à l'autre. Une passe simple perd ~1,5 % des titres
  et fabrique de faux « nouveaux ». Solution mesurée à 100 % : pages de 100 avec **pas de 50** (chevauchement) + **union**
  des deux tris `RATING_DESC` et `POPULARITY_DESC`, dédoublonnage par `id`. `DATE_RELEASE_DESC` est le pire (beaucoup de
  dates nulles).
- `providers[].webUrl` = lien de tracking JustWatch ; l'URL réelle (netflix.com/title/…, canalplus.com/…, mycanal.fr/…)
  est dans le paramètre `r=` → `direct_url()`.
- `providers` d'un produit peut ne pas contenir la plateforme interrogée (rare) : le script l'ajoute de force.
- `yearOfProduction` est souvent null pour les séries → repli sur l'année de `dateRelease`.
- Les **saisons n'ont pas de date** ; les **épisodes** oui. Date de la dernière saison = `min(dateRelease)` des épisodes
  de la saison au plus grand `seasonNumber`. Des dates futures existent (saisons annoncées).
- `duration` en secondes ; pour une série = durée d'un épisode.
- Rythme : 0,3 s entre pages, tout le catalogue (8 plateformes × 2 univers) ≈ 8 min, ~250 requêtes. Pas de blocage observé.

## Catégories (`category`) → formats
- Films : `Film`, `Téléfilm`, `Film VOD`, `Film DTV`, `Moyen-métrage` → film ; `Long/Court/Moyen-métrage d'animation` ou genre
  `Animation` → animation ; `Documentaire`, `Documentaire TV`, `Court-métrage documentaire` → documentaire ; `Spectacle`,
  `Concert` → spectacle (stand-up !) ; `Court-métrage` → court.
- Séries : `Série`, `Drama`, `Websérie`, `Série audio` → serie ; `Anime (mangas)`, `Dessin animé (cartoons)`, `OAV` ou genre
  `Animation` → animation ; genre `Documentaire` → documentaire ; `Émission TV/Web` ou genres `Télé-réalité`, `Talk Show`,
  `Jeu télévisé & divertissement` → emission.
- Genres séries spécifiques : `Mini-série`, `Judiciaire`, `Médical`, `Shōnen`, `Seinen`, `Anthologique`, `Épouvante-horreur`
  (minuscule h, ≠ films). Le mapping thèmes en tient compte.

## Autres queries utiles (non utilisées par le site)
- `product(id:Int)` : fiche complète (mêmes champs + `providers`, `productionStatus`, `originalRun`, `vodPlatforms`…).
- `products(ids:[Int])` : plusieurs fiches d'un coup (100 ok).
- `results(query:String, filters:[{identifier:"universe", value:"movie"}]) { hits(page:{size}) { items { id ... on
  ResultHit { fields { title year url } } } } }` : recherche plein texte (Searchkit). Pas de facette plateforme.
- Schéma approximatif communautaire : github.com/SilentVoid13/critique.rs (`critique_api/gql/schema.graphql`).

## Alternative si SC casse
JustWatch GraphQL `POST https://apis.justwatch.com/graphql` (sans auth) : `popularTitles(country:"FR", filter:{packages:
["nfx"|"cpd"|"prv"|"dnp"], objectTypes:[MOVIE], monetizationTypes:[FLATRATE]})`. Donne la dispo mais **pas la note SC** ;
il faudrait alors matcher titre+année via `results(query:)` puis `product(id)`. Couverture JW > SC d'environ 20 % sur Canal+.
