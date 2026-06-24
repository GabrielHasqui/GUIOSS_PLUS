import requests
from django.conf import settings

from apps.literature.constants import MIN_PUBLICATION_YEAR


OPENALEX_WORKS_URL = "https://api.openalex.org/works"


def search_openalex_works(query, per_page=10):
    params = {
        "search": query,
        "filter": f"from_publication_date:{MIN_PUBLICATION_YEAR}-01-01",
        "per-page": per_page,
        "sort": "cited_by_count:desc",
    }

    if settings.OPENALEX_EMAIL:
        params["mailto"] = settings.OPENALEX_EMAIL

    if settings.OPENALEX_API_KEY:
        params["api_key"] = settings.OPENALEX_API_KEY

    response = requests.get(
        OPENALEX_WORKS_URL,
        params=params,
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    return data.get("results", [])
