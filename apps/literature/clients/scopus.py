import requests
from django.conf import settings


SCOPUS_SEARCH_URL = "https://api.elsevier.com/content/search/scopus"


def search_scopus_works(query, per_page=10):
    if not settings.SCOPUS_API_KEY:
        raise ValueError("SCOPUS_API_KEY no esta configurada en .env")

    params = {
        "query": query,
        "count": per_page,
        "sort": "-citedby-count",
        "view": "STANDARD",
    }
    headers = {
        "Accept": "application/json",
        "X-ELS-APIKey": settings.SCOPUS_API_KEY,
    }

    response = requests.get(
        SCOPUS_SEARCH_URL,
        params=params,
        headers=headers,
        timeout=25,
    )
    response.raise_for_status()

    data = response.json()
    return data.get("search-results", {}).get("entry", [])
