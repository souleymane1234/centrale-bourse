"""
Extraction PDG / PCA / DG depuis textes de gouvernance Sikafinance (formats hétérogènes).
"""
import re
import unicodedata

_INVALID_EXECUTIVE_NAMES = frozenset(
    {
        "dirigeants",
        "dirigeant",
        "n/a",
        "na",
        "non renseigne",
        "non renseigné",
    }
)


def _normalize_text(value):
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


def normalize_governance_raw(raw_text):
    """Retire l'en-tête de section Sikafinance (« Dirigeants ») du bloc brut."""
    if not raw_text:
        return ""
    text = _normalize_text(raw_text)
    text = re.sub(r"^[:\s]+", "", text)
    text = re.sub(r"^Dirigeants?\s*:?\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def is_valid_executive_name(name):
    if not name:
        return False
    normalized = _normalize_text(name).lower()
    if normalized in _INVALID_EXECUTIVE_NAMES:
        return False
    if re.fullmatch(r"dirigeants?", normalized):
        return False
    return len(normalized) >= 3


def _clean_person_name(name):
    if not name:
        return None
    cleaned = _normalize_text(name)
    cleaned = re.sub(
        r"^(?:Mr|Mme|M\.|Mrs?\.?|Monsieur|Madame|Dr\.?)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s*[-–]\s*DG\s*:.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\s+(?=(?:Directeur|Directrice|Secrétaire|Administrateur)\s+"
        r"(?:Général|General|Adjoint|adjointe?|financier|Générale|Generale)\b).*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", cleaned).strip(" ,;.-")
    if not is_valid_executive_name(cleaned):
        return None
    if re.search(r"\b(?:Administrateur|Groupe|Finance)\b", cleaned, re.I):
        return None
    return cleaned


def _match_first(patterns, text, group=1):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            name = _clean_person_name(match.group(group))
            if name:
                return name
    return None


_CHAIRMAN_PATTERNS = [
    r"Président\s+du\s+Conseil\s+d['\u2019]Administration[^:]*:\s*"
    r"(?:Mr|Mme|M\.|Mrs?\.?)?\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-\.\s]+?)"
    r"(?=\s+Directeur|\s+DG\b|\s+PDG\b|\s+Administrateur|$)",
    r"\bPCA\s*:\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-\.\s]+?)(?=\s+DG\b|\s+PDG\b|\s+Directeur|$)",
    r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-\.\s]+?)\s+Chairman\b",
    r"(?:Mr|Mme|Monsieur|Madame)\s+([A-Za-zÀ-ÿ][\w\s\-\.]+?)\s*\(\s*Président\s*\)",
]

_CEO_PATTERNS = [
    r"DG\s+NSIA\s+BANQUE\s*:\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-\.\s]+?)(?=\s|$)",
    r"(?:PDG|Directeur\s+G[eéè]n[eéè]ral(?:e)?(?!\s+Adjoint)(?:\s+du\s+Groupe)?|"
    r"Directrice\s+G[eéè]n[eéè]rale(?!\s+Adjoint)|"
    r"Direction\s+G[eéè]n[eéè]rale|Managing\s+Director)\s*[^:]*:\s*"
    r"(?:Mr|Mme|M\.|Mrs?\.?|-\s*)?\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-\.\s]+?)"
    r"(?=\s*(?:DG\b|PCA\b|Directeur|Directrice|Président|Group|Administrateur|\(|$|;))",
    r"\bDG\s*:\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-\.\s]+?)"
    r"(?=\s*(?:DG\b|PCA\b|Directeur|Président|\(|$|;))",
    r"Président\s+Directeur\s+G[eé]n[eé]ral\s*:\s*"
    r"(?:Mr|Mme|M\.|Mrs?\.?)?\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-\.\s]+?)(?=\s|$)",
    r"(?:Mr|Mme|Monsieur|Madame)\s+([A-Za-zÀ-ÿ][\w\s\-\.]+?)\s*\(\s*Directeur\s+G[eé]n[eé]ral\s*\)",
    r"(?!Dirigeants?\b)([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-\.\s]+?)\s*,?\s*Directeur\s+g[eéè]n[eéè]ral\b",
    r"(?!Dirigeants?\b)([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-\.\s]+?)\s+Directeur\s+G[eéè]n[eéè]ral\b(?!\s+Adjoint)",
    r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-\.\s]+?)\s+Managing\s+Director\b",
]


def extract_executives_from_raw(raw_text):
    """Retourne (chairman, chief_executive) depuis un bloc Dirigeants Sikafinance."""
    if not raw_text:
        return None, None

    text = normalize_governance_raw(raw_text)
    if not text:
        return None, None

    chairman = _match_first(_CHAIRMAN_PATTERNS, text)
    chief_executive = _match_first(_CEO_PATTERNS, text)

    if not chief_executive:
        pdg_role = re.search(
            r"Président\s+Directeur\s+G[eé]n[eé]ral\s*:\s*"
            r"(?:Mr|Mme|M\.|Mrs?\.?)?\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-\.\s]+?)(?=\s|$)",
            text,
            flags=re.IGNORECASE,
        )
        if pdg_role:
            chief_executive = _clean_person_name(pdg_role.group(1))
            if chief_executive and not chairman:
                chairman = chief_executive

    if not chief_executive and not re.search(
        r"Directeur|Directrice|PDG|\bDG\b|PCA|Managing|Président",
        text,
        flags=re.IGNORECASE,
    ):
        chief_executive = _clean_person_name(text)

    return chairman, chief_executive


def enrich_governance(governance):
    """Complète chairman / chief_executive / roles manquants à partir du texte brut."""
    if not governance:
        return governance

    raw = normalize_governance_raw(governance.get("raw") or "")
    roles = list(governance.get("roles") or [])

    chairman = governance.get("chairman")
    chief_executive = governance.get("chief_executive")

    parsed_chair, parsed_ceo = extract_executives_from_raw(raw)
    if not chairman and parsed_chair:
        chairman = parsed_chair
    if not chief_executive and parsed_ceo:
        chief_executive = parsed_ceo

    if raw and not roles:
        roles = _parse_roles_from_raw(raw)

    if not chief_executive:
        chief_executive = _pick_role_name(
            roles,
            [
                "directeur general",
                "directrice generale",
                "pdg",
                "dg",
                "direction generale",
                "managing director",
            ],
        )
    if not chairman:
        chairman = _pick_role_name(
            roles,
            [
                "pca",
                "president du conseil",
                "chairman",
                "president directeur general",
            ],
        )

    if chairman and not is_valid_executive_name(chairman):
        chairman = None
    if chief_executive and not is_valid_executive_name(chief_executive):
        chief_executive = None

    result = dict(governance)
    result["raw"] = raw or governance.get("raw")
    result["chairman"] = chairman
    result["chief_executive"] = chief_executive
    result["roles"] = roles
    return result


def _pick_role_name(roles, wanted_labels):
    wanted = set(wanted_labels)
    for entry in roles or []:
        role_key = _normalize_text(entry.get("role") or "").lower()
        if "adjoint" in role_key:
            continue
        if any(label in role_key for label in wanted):
            name = _clean_person_name(entry.get("name"))
            if name:
                return name
    return None


def _parse_roles_from_raw(raw_text):
    """Découpe les rôles « Label : Nom » y compris formes abrégées (DG, PCA)."""
    if not raw_text:
        return []

    text = _normalize_text(raw_text)
    labels = [
        "Président directeur général",
        "Président du Conseil d'Administration",
        "Président du conseil d'administration",
        "Direction Générale",
        "Direction generale",
        "PCA",
        "PDG",
        "DG",
        "Directeur Général Adjoint",
        "Directeur Général",
        "Directrice Générale",
        "Directeur general",
        "Directrice generale",
        "Directeur financier",
        "Managing Director",
        "Chairman",
    ]

    pattern = r"(" + "|".join(re.escape(label) for label in labels) + r")\s*:\s*"
    matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
    roles = []

    for index, match in enumerate(matches):
        role = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        person = text[start:end]
        person = re.sub(
            r"\b(Nombre de titres|Flottant|Valorisation).*$",
            "",
            person or "",
            flags=re.IGNORECASE,
        )
        person = _clean_person_name(person)
        if person:
            roles.append({"role": role, "name": person})

    return roles
