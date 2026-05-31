"""
Extraction actif / capitaux propres / dettes depuis les PDF BRVM (états financiers).
"""
import io
import re
from datetime import datetime, timezone

import pdfplumber

# Libellés bilan (SYSCOHADA, IFRS, banques) — ordre = priorité
ASSET_PATTERNS = [
    r"TOTAL\s+(?:DE\s+L['']?\s*)?ACTIF\b",
    r"Total\s+actif\b",
]

EQUITY_PATTERNS = [
    r"CAPITAUX\s+PROPRES(?:\s+ET\s+RESSOURCES\s+ASSIMILEES)?\b",
    r"Total\s+des\s+capitaux\s+propres\b",
    r"(?:^|\s)CAPITAUX\s+PROPRES\b",
]

LIABILITY_PATTERNS = [
    r"TOTAL\s+PASSIF",
    r"Total\s+Passif\b",
    r"TOTAL\s+DU\s+PASSIF",
]

DEBT_PATTERNS = [
    r"TOTAL\s+DETTES",
    r"Total\s+des\s+dettes",
    r"DETTES\s+FINANCIERES",
]


def _normalize_label(text):
    if not text:
        return ""
    value = str(text).lower()
    value = value.replace("’", "'").replace("'", "'")
    value = (
        value.replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ô", "o")
    )
    return re.sub(r"\s+", " ", value).strip()


def parse_amount_token(raw):
    """Convertit un montant BRVM (espaces / virgules) en float (millions FCFA)."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text in {"-", "—", "–", "n/a", "na"}:
        return None

    text = text.replace("\xa0", " ").strip()
    if re.fullmatch(r"\d{1,3}(?:[ \u00a0]\d{3})+(?:[.,]\d+)?", text):
        text = re.sub(r"[ \u00a0]", "", text)
    else:
        text = text.replace(" ", "")

    if re.fullmatch(r"\d{1,3}(?:,\d{3})+", text):
        text = text.replace(",", "")
    elif "," in text and "." in text:
        text = text.replace(",", "")
    elif "," in text:
        parts = text.split(",")
        if len(parts) == 2 and len(parts[1]) == 3:
            text = parts[0] + parts[1]
        else:
            text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def _strip_line_number_prefix(line):
    """Retire le numéro de poste en début de ligne (ex. « 9 CAPITAUX PROPRES »)."""
    return re.sub(r"^\d+\s+", "", (line or "").strip())


def _amounts_after_label_tail(tail):
    """Extrait les montants (millions FCFA) après le libellé, hors pourcentages."""
    if not tail:
        return []

    cleaned = re.sub(r"[-+]?\d+(?:[.,]\d+)?\s*%", "", tail)
    values = []

    # Montants en millions : « 183 993 » (deux blocs numériques).
    for token in re.findall(r"\d{1,3}[ \u00a0]\d{3}", cleaned):
        parsed = parse_amount_token(token)
        if parsed is not None and parsed >= 100:
            values.append(parsed)

    return values[:2]


def _match_line_value(lines, patterns):
    for line in lines:
        stripped = _strip_line_number_prefix(line)
        normalized = _normalize_label(stripped)
        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if not match:
                continue
            amounts = _amounts_after_label_tail(normalized[match.end() :])
            if amounts:
                return amounts
    return []


def infer_report_year(pdf_url=None, pdf_title=None):
    for source in (pdf_url or "", pdf_title or ""):
        match = re.search(r"(?:exercice|annee|year|[_\s-])(20\d{2})", source, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def parse_balance_sheet_text(text, report_year=None, pdf_url=None):
    """
    Extrait les postes bilan d'un texte PDF.
    Retourne une liste d'exercices (année la plus récente en premier).
    """
    if not text or len(text.strip()) < 200:
        return []

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    year = report_year or infer_report_year(pdf_url=pdf_url)

    assets = _match_line_value(lines, ASSET_PATTERNS)
    equity = _match_line_value(lines, EQUITY_PATTERNS)
    liabilities = _match_line_value(lines, LIABILITY_PATTERNS)
    explicit_debt = _match_line_value(lines, DEBT_PATTERNS)

    if not assets and not equity and not liabilities:
        return []

    lengths = [len(assets), len(equity), len(liabilities), len(explicit_debt)]
    max_len = max(lengths) if lengths else 0
    if max_len == 0:
        return []

    entries = []
    for index in range(max_len):
        entry_year = year - index if year else None
        total_assets = assets[index] if index < len(assets) else None
        equity_mfcfa = equity[index] if index < len(equity) else None
        total_liabilities = liabilities[index] if index < len(liabilities) else None
        debt_mfcfa = explicit_debt[index] if index < len(explicit_debt) else None

        computed_debt = None
        if total_liabilities is not None and equity_mfcfa is not None:
            computed_debt = max(total_liabilities - equity_mfcfa, 0)

        if computed_debt is not None:
            if debt_mfcfa is None or debt_mfcfa < computed_debt * 0.5:
                debt_mfcfa = computed_debt

        if not any([total_assets, equity_mfcfa, debt_mfcfa, total_liabilities]):
            continue

        entries.append(
            {
                "year": entry_year,
                "total_assets_mfcfa": round(total_assets, 2) if total_assets is not None else None,
                "equity_mfcfa": round(equity_mfcfa, 2) if equity_mfcfa is not None else None,
                "debt_mfcfa": round(debt_mfcfa, 2) if debt_mfcfa is not None else None,
                "total_liabilities_mfcfa": round(total_liabilities, 2)
                if total_liabilities is not None
                else None,
            }
        )

    return entries


def parse_balance_sheet_pdf(pdf_bytes, pdf_url=None, pdf_title=None, max_pages=12):
    """Parse un PDF BRVM et retourne l'historique bilan détecté."""
    if not pdf_bytes:
        return []

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as document:
            pages = document.pages[:max_pages]
            text = "\n".join((page.extract_text() or "") for page in pages)
    except Exception:
        return []

    report_year = infer_report_year(pdf_url=pdf_url, pdf_title=pdf_title)
    entries = parse_balance_sheet_text(text, report_year=report_year, pdf_url=pdf_url)
    scraped_at = datetime.now(timezone.utc).isoformat()

    for entry in entries:
        entry["source"] = "brvm_pdf"
        entry["pdf_url"] = pdf_url
        entry["scraped_at"] = scraped_at

    return entries


def merge_balance_sheet_history(existing, new_entries):
    """Fusionne les exercices par année (garde le plus récent scrape)."""
    by_year = {}

    for entry in existing or []:
        year = entry.get("year")
        if year is not None:
            by_year[int(year)] = dict(entry)

    for entry in new_entries or []:
        year = entry.get("year")
        if year is None:
            continue
        by_year[int(year)] = dict(entry)

    return sorted(by_year.values(), key=lambda item: item.get("year") or 0, reverse=True)


def get_latest_balance_sheet(company):
    history = (company or {}).get("balance_sheet_history") or []
    if not history:
        return None
    return max(history, key=lambda item: item.get("year") or 0)
