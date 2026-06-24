from apps.literature.constants import MIN_PUBLICATION_YEAR


MIN_DOCUMENT_RELEVANCE_SCORE = 5
UNTITLED_MARKERS = {
    "",
    "untitled scopus work",
    "untitled openalex work",
    "untitled work",
}


def text_contains_any(text, terms):
    text = (text or "").lower()

    for term in terms:
        if term.lower() in text:
            return True

    return False


def has_meaningful_title(title):
    return (title or "").strip().lower() not in UNTITLED_MARKERS


def has_meaningful_identifier(identifier):
    return bool((identifier or "").strip())


def is_usable_literature_result(title, identifier, relevance_score):
    """
    Evita que entradas incompletas o apenas tangenciales alimenten la IL.
    """
    return (
        has_meaningful_title(title)
        and has_meaningful_identifier(identifier)
        and relevance_score >= MIN_DOCUMENT_RELEVANCE_SCORE
    )


def calculate_document_relevance_score(work, evaluation, factor):
    title = work.get("display_name") or ""
    keywords = list(factor.keywords.values_list("keyword", flat=True))

    score = 0

    if text_contains_any(title, [evaluation.software_name]):
        score += 2

    if text_contains_any(title, keywords):
        score += 3

    if text_contains_any(
        title,
        [
            "open source",
            "free software",
            "floss",
            "oss",
            "adoption",
            "migration",
        ],
    ):
        score += 2

    citations = work.get("cited_by_count") or 0

    if citations >= 100:
        score += 2
    elif citations >= 25:
        score += 1

    return score


def calculate_scopus_document_relevance_score(entry, evaluation, factor):
    title = entry.get("dc:title") or ""
    source_title = entry.get("prism:publicationName") or ""
    text = f"{title} {source_title}"
    keywords = list(factor.keywords.values_list("keyword", flat=True))

    # Scopus searched TITLE-ABS-KEY, so a returned result is already a
    # signal that the factor appeared in title, abstract, or keywords.
    score = 3

    if text_contains_any(text, [evaluation.software_name]):
        score += 2

    if text_contains_any(text, keywords):
        score += 3

    if text_contains_any(
        text,
        [
            "open source",
            "free software",
            "floss",
            "oss",
            "adoption",
            "migration",
        ],
    ):
        score += 2

    citations = int(entry.get("citedby-count") or 0)

    if citations >= 100:
        score += 2
    elif citations >= 25:
        score += 1

    return score


def normalize_context_for_search(context):
    context_map = {
        "Educación": "education",
        "Educacion": "education",
        "Salud": "health",
        "Gobierno": "government",
        "Empresa": "enterprise",
        "Organización": "organization",
        "Organizacion": "organization",
    }

    return context_map.get(context, context)


def build_openalex_query(evaluation, factor):
    keywords = list(
        factor.keywords.values_list("keyword", flat=True)
    )

    main_keyword = keywords[0] if keywords else factor.name
    context = normalize_context_for_search(evaluation.context)

    return (
        f"{evaluation.software_name} {context} "
        f"open source software adoption {main_keyword}"
    )


def build_scopus_query(evaluation, factor):
    keywords = list(factor.keywords.values_list("keyword", flat=True))
    selected_keywords = keywords[:3] or [factor.name]
    context = normalize_context_for_search(evaluation.context)
    keyword_query = " OR ".join(f'"{keyword}"' for keyword in selected_keywords)

    terms = (
        f'"{evaluation.software_name}" AND ({keyword_query}) AND '
        f'({context} OR adoption OR "open source" OR FLOSS OR OSS)'
    )

    return (
        f"TITLE-ABS-KEY({terms}) AND "
        f"PUBYEAR > {MIN_PUBLICATION_YEAR - 1}"
    )
