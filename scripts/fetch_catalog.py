#!/usr/bin/env python3
"""ZazzuList — récupération du catalogue (films + séries) par plateforme.

Interroge l'API GraphQL publique de SensCritique (streamingExplorer) et écrit un
fichier JSON par univers et par plateforme dans docs/data/ :
    docs/data/films_1.json, docs/data/series_1.json, ...  (1 = Netflix, etc.)
    docs/data/manifest.json                                (plateformes, dates)

La page docs/index.html ne charge que les fichiers des plateformes de l'utilisateur.
Lancé chaque nuit par GitHub Actions ; aucune dépendance hors bibliothèque standard.

Usage : python scripts/fetch_catalog.py [films|series] [--providers 1,4]
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "docs", "data")

SC_ENDPOINT = "https://apollo.senscritique.com/"
SC_SITE = "https://www.senscritique.com"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Plateformes proposées (id SensCritique -> nom). Autres ids connus : OCS 3,
# Apple TV+ 6, France TV 9, Arte 18, Paramount+ 19, MUBI 20, M6+ 26, TF1+ 27, MAX 28.
PROVIDERS = {
    1: "Netflix",
    4: "Canal+",
    2: "Prime Video",
    7: "Disney+",
}
UNIVERSES = {"films": "movie", "series": "tvShow"}

MIN_RATING = 6
PAGE_SIZE = 100
PAGE_DELAY = 0.3
# Pagination SC instable sur les ex-æquo : pages chevauchées + union de deux tris.
PAGE_STEP = 50
ORDERS = ("RATING_DESC", "POPULARITY_DESC")

QUERY = """
query StreamingExplorer($providers: [Int], $rating: [Int], $subtype: String!,
                        $limit: Int, $offset: Int, $order: StreamingSort) {
  streamingExplorer(providers: $providers, rating: $rating, subtype: $subtype,
                    limit: $limit, offset: $offset, order: $order) {
    total
    products {
      id title originalTitle yearOfProduction dateRelease rating duration genres category synopsis url
      directors { name }
      creators { name }
      seasons { seasonNumber episodes { dateRelease } }
      countries { name }
      medias { picture }
      stats { ratingCount }
      providers { providerId name webUrl }
    }
  }
}
"""

CONTINENTS = {
    "Amérique du Nord": ["États-Unis", "Canada", "Bermudes"],
    "Amérique latine": ["Mexique", "Brésil", "Argentine", "Chili", "Colombie", "Haïti", "Équateur", "Uruguay",
                        "Pérou", "Cuba", "Venezuela", "Bolivie", "Paraguay", "Guatemala", "Costa Rica",
                        "République dominicaine", "Porto Rico", "Jamaïque", "Panama", "Nicaragua", "Honduras",
                        "Salvador"],
    "Europe": ["France", "Royaume-Uni", "Italie", "Allemagne", "République fédérale d'Allemagne", "Espagne",
               "Belgique", "Suède", "Danemark", "Norvège", "Pologne", "Suisse", "Pays-Bas", "Irlande", "Finlande",
               "Autriche", "Islande", "Grèce", "Luxembourg", "Serbie", "Hongrie", "Roumanie", "Ukraine", "Portugal",
               "Tchéquie", "République tchèque", "Lituanie", "Russie", "Croatie", "Bulgarie", "Slovaquie",
               "Slovénie", "Estonie", "Lettonie", "Bosnie-Herzégovine", "Macédoine du Nord", "Monténégro",
               "Albanie", "Biélorussie", "Moldavie", "Malte", "Chypre", "URSS", "Yougoslavie", "Tchécoslovaquie",
               "République démocratique allemande", "Écosse", "Kosovo", "Pays de Galles", "Irlande du Nord",
               "Andorre", "Monaco", "Liechtenstein"],
    "Asie": ["Inde", "Japon", "Corée du Sud", "Taïwan", "Chine", "Hong Kong", "Turquie", "Iran", "Thaïlande",
             "Israël", "Cambodge", "Qatar", "Malaisie", "Vietnam", "Indonésie", "Pakistan", "Liban", "Bangladesh",
             "Philippines", "Géorgie", "Afghanistan", "Arabie saoudite", "Jordanie", "Kazakhstan", "Singapour",
             "Sri Lanka", "Népal", "Mongolie", "Corée du Nord", "Émirats arabes unis", "Irak", "Syrie", "Palestine",
             "Arménie", "Azerbaïdjan", "Ouzbékistan", "Kirghizistan", "Birmanie", "Myanmar", "Laos", "Bhoutan",
             "Koweït", "Yémen", "Oman", "Bahreïn", "Tadjikistan", "Macao", "Brunei", "Timor oriental"],
    "Afrique": ["Afrique du Sud", "Congo", "Tunisie", "Maroc", "Égypte", "Algérie", "Sénégal", "Nigeria", "Kenya",
                "Mali", "Burkina Faso", "Côte d'Ivoire", "Cameroun", "Ghana", "Éthiopie", "Rwanda", "Ouganda",
                "Tanzanie", "Mozambique", "Angola", "Zimbabwe", "Madagascar", "Mauritanie", "Niger", "Tchad",
                "Soudan", "Libye", "Somalie", "Bénin", "Togo", "Guinée", "Gabon", "République démocratique du Congo",
                "Zambie", "Namibie", "Botswana", "Maurice", "Cap-Vert", "Érythrée", "Djibouti", "Malawi",
                "Sierra Leone", "Liberia", "Burundi", "Seychelles", "Comores", "Gambie", "Guinée-Bissau",
                "Guinée équatoriale", "République centrafricaine", "Lesotho", "Eswatini", "Soudan du Sud"],
    "Océanie": ["Australie", "Nouvelle-Zélande", "Fidji", "Papouasie-Nouvelle-Guinée", "Samoa", "Tahiti",
                "Polynésie française", "Nouvelle-Calédonie", "Vanuatu", "Tonga"],
}
COUNTRY_TO_CONTINENT = {c: k for k, cs in CONTINENTS.items() for c in cs}
_unknown_countries = set()


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def sc_query(variables, retries=3):
    body = json.dumps({"query": QUERY, "variables": variables}).encode("utf-8")
    req = urlrequest.Request(SC_ENDPOINT, data=body, method="POST", headers={
        "Content-Type": "application/json", "Accept": "application/json", "User-Agent": USER_AGENT,
        "Origin": SC_SITE, "Referer": SC_SITE + "/films/streaming"})
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with urlrequest.urlopen(req, timeout=60) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            if payload.get("errors"):
                raise RuntimeError(json.dumps(payload["errors"], ensure_ascii=False)[:500])
            return payload["data"]
        except (HTTPError, URLError, TimeoutError, RuntimeError) as err:
            last_err = err
            if isinstance(err, HTTPError) and 400 <= err.code < 500:
                break
            if attempt < retries:
                wait = 3 * attempt
                log(f"  erreur ({err}), nouvel essai dans {wait}s...")
                time.sleep(wait)
    raise RuntimeError(f"SensCritique injoignable : {last_err}")


def direct_url(web_url):
    """webUrl SC = lien de tracking JustWatch ; la cible réelle est dans ?r=."""
    if not web_url:
        return None
    try:
        target = parse_qs(urlparse(web_url).query).get("r")
        if target and target[0].startswith("http"):
            return target[0]
    except ValueError:
        pass
    return web_url


def format_of(category, genres, subtype):
    cat = (category or "").lower()
    genres = set(genres or [])
    if subtype == "tvShow":
        if "Documentaire" in genres or "documentaire" in cat:
            return "documentaire"
        if "mission" in cat or genres & {"Télé-réalité", "Talk Show", "Jeu télévisé & divertissement"}:
            return "emission"
        if "anim" in cat or "oav" in cat or "Animation" in genres:
            return "animation"
        return "serie"
    if "spectacle" in cat or cat in ("concert", "émission", "emission"):
        return "spectacle"
    if "animation" in cat or "Animation" in genres:
        return "animation"
    if "documentaire" in cat:
        return "documentaire"
    if "court" in cat:
        return "court"
    return "film"


def continent_of(countries):
    if not countries:
        return None
    cont = COUNTRY_TO_CONTINENT.get(countries[0])
    if cont is None:
        _unknown_countries.add(countries[0])
    return cont


def last_season(seasons):
    dated = []
    for season in seasons or []:
        dates = [e["dateRelease"] for e in (season.get("episodes") or []) if e.get("dateRelease")]
        if dates and season.get("seasonNumber"):
            dated.append((season["seasonNumber"], min(dates)))
    if not dated:
        return None, None
    return max(dated)


def year_of(date_str):
    try:
        return int(str(date_str)[:4]) if date_str else None
    except ValueError:
        return None


def normalize(product, subtype):
    countries = [c["name"] for c in (product.get("countries") or []) if c.get("name")]
    people = product.get("directors") or product.get("creators") or []
    medias = product.get("medias") or {}
    stats = product.get("stats") or {}
    item = {
        "id": product["id"],
        "title": product.get("title"),
        "original_title": product.get("originalTitle"),
        "year": product.get("yearOfProduction") or year_of(product.get("dateRelease")),
        "rating": product.get("rating"),
        "votes": stats.get("ratingCount") or 0,
        "duration_min": round(product["duration"] / 60) if product.get("duration") else None,
        "genres": product.get("genres") or [],
        "format": format_of(product.get("category"), product.get("genres"), subtype),
        "directors": [d["name"] for d in people if d.get("name")][:3],
        "country": countries[0] if countries else None,
        "continent": continent_of(countries),
        "synopsis": product.get("synopsis"),
        "poster": medias.get("picture"),
        "sc_url": SC_SITE + product["url"] if product.get("url") else None,
        # toutes les plateformes connues du titre (parmi PROVIDERS) : la page filtre selon l'utilisateur
        "platforms": [{"id": p["providerId"], "url": direct_url(p.get("webUrl"))}
                      for p in (product.get("providers") or []) if p.get("providerId") in PROVIDERS],
    }
    if subtype == "tvShow":
        number, date = last_season(product.get("seasons"))
        item.update({"seasons": len(product.get("seasons") or []) or None,
                     "last_season": number, "last_season_date": date})
    return item


def fetch_platform(provider_id, subtype):
    name = PROVIDERS[provider_id]
    page_size, step = PAGE_SIZE, PAGE_STEP
    found = {}
    for order in ORDERS:
        offset, total = 0, None
        while total is None or offset < total:
            variables = {"providers": [provider_id], "rating": [MIN_RATING, 10], "subtype": subtype,
                         "order": order, "limit": page_size, "offset": offset}
            try:
                data = sc_query(variables)
            except RuntimeError as err:
                if page_size > 20 and "invalid-params" in str(err):
                    page_size, step = 20, 10
                    continue
                raise
            result = data["streamingExplorer"]
            if result is None:
                raise RuntimeError("streamingExplorer a renvoyé null")
            total = result["total"]
            products = result["products"] or []
            for product in products:
                found[product["id"]] = product
            log(f"  {name} {subtype} ({order}): {min(offset + len(products), total)}/{total} — {len(found)} uniques")
            if len(products) < page_size:
                break
            offset += step
            time.sleep(PAGE_DELAY)
    return list(found.values())


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def build(universe, provider_id):
    subtype = UNIVERSES[universe]
    path = os.path.join(DATA_DIR, f"{universe}_{provider_id}.json")
    previous = read_json(path, None)
    # first_seen : conservé d'un passage à l'autre ; inconnu (null) au tout premier passage,
    # pour ne pas marquer "nouveau" tout le catalogue.
    previous_seen = {t["id"]: t.get("first_seen") for t in (previous or {}).get("titles", [])}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    titles = []
    for product in fetch_platform(provider_id, subtype):
        item = normalize(product, subtype)
        if not any(p["id"] == provider_id for p in item["platforms"]):
            item["platforms"].append({"id": provider_id, "url": None})
        item["first_seen"] = previous_seen.get(item["id"], now if previous else None)
        titles.append(item)
    titles.sort(key=lambda t: (-(t["rating"] or 0), -(t["votes"] or 0)))
    write_json(path, {"universe": universe, "provider": provider_id, "fetched_at": now, "titles": titles})
    log(f"{path}: {len(titles)} titres")
    return len(titles)


def main(argv):
    universes = [a for a in argv if a in UNIVERSES] or list(UNIVERSES)
    providers = list(PROVIDERS)
    if "--providers" in argv:
        providers = [int(x) for x in argv[argv.index("--providers") + 1].split(",")]
    started = time.time()
    counts = {}
    for universe in universes:
        for provider_id in providers:
            log(f"Récupération {PROVIDERS[provider_id]} / {universe}...")
            counts[f"{universe}_{provider_id}"] = build(universe, provider_id)
    manifest = read_json(os.path.join(DATA_DIR, "manifest.json"), {})
    manifest.update({
        "providers": [{"id": pid, "name": name} for pid, name in PROVIDERS.items()],
        "universes": list(UNIVERSES),
        "min_rating": MIN_RATING,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "counts": {**manifest.get("counts", {}), **counts},
    })
    write_json(os.path.join(DATA_DIR, "manifest.json"), manifest)
    if _unknown_countries:
        log(f"Pays inconnus (à ajouter dans CONTINENTS) : {sorted(_unknown_countries)}")
    log(f"Terminé en {time.time() - started:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
