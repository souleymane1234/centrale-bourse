import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from urllib.parse import urljoin

import requests
import urllib3

VENDOR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.vendor')
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)

from bs4 import BeautifulSoup
import cloudscraper


class CompanyInfoScraper:
    BRVM_BASE_URL = "https://www.brvm.org"
    BRVM_DIRECTORY_URL = f"{BRVM_BASE_URL}/en/emetteurs/societes-cotees"
    BRVM_REPORTS_URL = f"{BRVM_BASE_URL}/en/rapports-societes-cotees"
    SIKAFINANCE_QUOTES_URL = "https://www.sikafinance.com/marches/aaz"
    SIKAFINANCE_PALMARES_URL = "https://www.sikafinance.com/marches/palmares"

    def __init__(self, timeout=30, verify_brvm_ssl=False):
        self.timeout = timeout
        self.verify_brvm_ssl = verify_brvm_ssl
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }

        self.brvm_session = requests.Session()
        self.brvm_session.headers.update(self.headers)

        self.sikafinance_session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "darwin", "desktop": True}
        )
        self.sikafinance_session.headers.update(self.headers)

        if not self.verify_brvm_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def scrape_all_company_data(self):
        directory_companies = self.fetch_brvm_directory()
        reports_reference = self.fetch_brvm_reports_reference()
        sikafinance_payload = self.fetch_sikafinance_market_data()

        companies = []
        for company in directory_companies:
            enriched = dict(company)

            try:
                enriched.update(self.fetch_brvm_company_profile(company["brvm_profile_url"]))
            except Exception as exc:
                enriched["profile_error"] = str(exc)

            report_entry = self.match_report_reference(enriched, reports_reference)
            if report_entry:
                enriched["brvm_reports_reference"] = report_entry
                self._attach_brvm_balance_sheet(enriched, report_entry)

            quote_entry = self.match_sikafinance_quote(
                enriched, sikafinance_payload["quotes"]
            )
            if quote_entry:
                enriched["market_quote"] = quote_entry
                self._attach_sikafinance_profile(enriched, quote_entry)

            companies.append(enriched)

        for reference in reports_reference:
            existing_company = self._find_existing_company(
                companies, self._text_aliases(reference.get("issuer"), reference.get("description"))
            )
            if existing_company:
                existing_company["brvm_reports_reference"] = reference
                self._attach_brvm_balance_sheet(existing_company, reference)
            else:
                companies.append(
                    {
                        "display_name": reference.get("description") or reference.get("issuer"),
                        "profile_name": reference.get("issuer"),
                        "brvm_reports_reference": reference,
                    }
                )

        for quote in sikafinance_payload["quotes"]:
            existing_company = self._find_existing_company(
                companies, self._text_aliases(quote.get("name"))
            )
            if existing_company:
                existing_company["market_quote"] = quote
                self._attach_sikafinance_profile(existing_company, quote)
            else:
                new_entry = {
                    "display_name": quote.get("name"),
                    "market_quote": quote,
                }
                self._attach_sikafinance_profile(new_entry, quote)
                companies.append(new_entry)

        companies = self._deduplicate_companies(companies)
        companies.sort(key=lambda item: item.get("display_name", ""))

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": {
                "brvm_directory_url": self.BRVM_DIRECTORY_URL,
                "brvm_reports_url": self.BRVM_REPORTS_URL,
                "sikafinance_quotes_url": self.SIKAFINANCE_QUOTES_URL,
            },
            "market_indices": sikafinance_payload["indices"],
            "quotes_count": len(sikafinance_payload["quotes"]),
            "companies_count": len(companies),
            "companies": companies,
        }

    def fetch_brvm_directory(self):
        page_urls = [self.BRVM_DIRECTORY_URL]
        visited_pages = set()
        companies = []
        seen_profile_urls = set()

        while page_urls:
            page_url = page_urls.pop(0)
            if page_url in visited_pages:
                continue
            visited_pages.add(page_url)

            soup = self._get_brvm_soup(page_url)
            page_urls.extend(self._extract_directory_pagination_urls(soup))

            for block in soup.select("div.views-box-item"):
                title = self._clean_text(self._text_of(block.select_one(".title")))
                node_link = self._find_brvm_node_link(block)

                if not title or not node_link:
                    continue

                profile_url = urljoin(self.BRVM_BASE_URL, node_link)
                if profile_url in seen_profile_urls:
                    continue
                seen_profile_urls.add(profile_url)

                block_text = self._clean_text(block.get_text(" ", strip=True))
                companies.append(
                    {
                        "display_name": title,
                        "address": self._clean_text(self._text_of(block.select_one(".adresse_sgi"))),
                        "postal_address": self._clean_text(self._text_of(block.select_one(".bp"))),
                        "email": self._extract_email(block_text),
                        "phone": self._clean_text(self._text_of(block.select_one(".tel_sgi"))),
                        "fax": self._clean_text(self._text_of(block.select_one(".fax_sgi"))),
                        "website": self._extract_external_link(block),
                        "brvm_profile_url": profile_url,
                        "logo_url": self._extract_brvm_block_logo(block),
                    }
                )

        return companies

    def fetch_brvm_reports_reference(self):
        references = []
        page_urls = [self.BRVM_REPORTS_URL]
        visited_pages = set()

        while page_urls:
            page_url = page_urls.pop(0)
            if page_url in visited_pages:
                continue
            visited_pages.add(page_url)

            soup = self._get_brvm_soup(page_url)
            page_urls.extend(self._extract_reports_pagination_urls(soup))

            report_links = {}
            for anchor in soup.find_all("a", href=True):
                href = anchor["href"].strip()
                text = self._clean_text(anchor.get_text(" ", strip=True))
                if href.startswith("/en/rapports-societe-cotes/") and text:
                    report_links[self._normalize_key(text)] = urljoin(self.BRVM_BASE_URL, href)

            for table in soup.find_all("table"):
                rows = self._extract_table_rows(table)
                if not rows or rows[0][:3] != ["Code", "Issuer", "Description"]:
                    continue

                for row in rows[1:]:
                    if len(row) < 3:
                        continue
                    references.append(
                        {
                            "code": row[0],
                            "issuer": row[1],
                            "description": row[2],
                            "report_page_url": report_links.get(self._normalize_key(row[1])),
                        }
                    )

        return references

    def fetch_brvm_company_profile(self, profile_url):
        soup = self._get_brvm_soup(profile_url)
        paragraphs = [
            self._clean_text(paragraph.get_text(" ", strip=True))
            for paragraph in soup.find_all("p")
        ]
        tables = [self._extract_table_rows(table) for table in soup.find_all("table")]

        board_table = self._find_table(
            tables, lambda rows: rows and rows[0][:2] == ["Nom et Prénoms", "Fonction"]
        )
        shareholding_table = self._find_table(
            tables, lambda rows: rows and rows[0] and rows[0][0] == "Actionnariat"
        )
        financial_table = self._find_table(
            tables,
            lambda rows: rows
            and rows[0]
            and any("Chiffres d’affaires" in cell for cell in rows[0]),
        )

        website = self._extract_profile_website(soup)

        profile = {
            "profile_name": self._clean_text(self._text_of(soup.find("h1"))),
            "legal_name": self._extract_labeled_value(paragraphs, "Raison sociale"),
            "sector": self._extract_labeled_value(paragraphs, "Secteur d’activités"),
            "listing_date": self._extract_labeled_value(
                paragraphs, "Date d’introduction à la BRVM"
            ),
            "capital_social_raw": self._extract_labeled_value(paragraphs, "Capital social"),
            "symbol": self._extract_labeled_value(paragraphs, "Symbole"),
            "chairman": self._extract_labeled_value(
                paragraphs, "Président du conseil d’administration"
            ),
            "chief_executive": self._extract_labeled_value(
                paragraphs, "Directeur Général (ou équivalent)"
            ),
            "profile_website": website,
            "board_members": self._parse_board_members(board_table),
            "shareholding": self._parse_shareholding(shareholding_table),
            "financial_history": self._parse_financial_history(financial_table),
        }

        profile["capital_social"] = self._parse_number(profile["capital_social_raw"])
        if website and not profile.get("website"):
            profile["website"] = website

        return profile

    def fetch_sikafinance_market_data(self):
        soup = self._get_sikafinance_soup(self.SIKAFINANCE_QUOTES_URL)
        tables = soup.find_all("table")

        indices = []
        if tables:
            for tr in tables[0].find_all("tr")[1:]:
                cells = [
                    self._clean_text(cell.get_text(" ", strip=True))
                    for cell in tr.find_all(["th", "td"])
                ]
                if len(cells) < 6:
                    continue
                indices.append(
                    {
                        "name": cells[0],
                        "opening": self._parse_number(cells[1]),
                        "high": self._parse_number(cells[2]),
                        "low": self._parse_number(cells[3]),
                        "last": self._parse_number(cells[4]),
                        "variation_pct": self._parse_percentage(cells[5]),
                        "raw": cells,
                    }
                )

        quotes = []
        if len(tables) > 1:
            for tr in tables[1].find_all("tr")[1:]:
                cells = tr.find_all("td")
                if len(cells) < 8:
                    continue

                values = [self._clean_text(cell.get_text(" ", strip=True)) for cell in cells]
                quote_link = cells[0].find("a", href=True)
                details_url = None
                if quote_link:
                    href = quote_link["href"].strip()
                    if href.startswith("/marches/cotation_"):
                        details_url = urljoin(
                            self.SIKAFINANCE_QUOTES_URL,
                            href.replace("/marches/cotation_", "/marches/societe/"),
                        )
                    elif href.startswith("/marches/societe/"):
                        details_url = urljoin(self.SIKAFINANCE_QUOTES_URL, href)

                code = details_url.rsplit("/", 1)[-1] if details_url else None

                quotes.append(
                    {
                        "name": values[0],
                        "opening": self._parse_number(values[1]),
                        "high": self._parse_number(values[2]),
                        "low": self._parse_number(values[3]),
                        "volume_shares": self._parse_number(values[4]),
                        "volume_xof": self._parse_number(values[5]),
                        "last": self._parse_number(values[6]),
                        "variation_pct": self._parse_percentage(values[7]),
                        "source_url": self.SIKAFINANCE_QUOTES_URL,
                        "details_url": details_url,
                        "code": code,
                    }
                )

        return {"indices": indices, "quotes": quotes}

    def fetch_sikafinance_palmares(
        self,
        variation="h",
        market="br",
        since="yesterday",
        limit=None,
    ):
        """
        Palmarès Sikafinance (onglet Variation).
        variation: h = hausses, b = baisses
        """
        soup = self._post_sikafinance_palmares(
            variation=variation,
            market=market,
            since=since,
        )
        rows = self._parse_sikafinance_palmares_table(soup)
        if limit is not None:
            return rows[:limit]
        return rows

    def fetch_sikafinance_palmares_movers(
        self,
        market="br",
        since="yesterday",
        limit=30,
    ):
        """Retourne les listes hausses et baisses depuis le palmarès BRVM."""
        return {
            "gainers": self.fetch_sikafinance_palmares(
                variation="h", market=market, since=since, limit=limit
            ),
            "losers": self.fetch_sikafinance_palmares(
                variation="b", market=market, since=since, limit=limit
            ),
            "market": market,
            "since": since,
            "source_url": self.SIKAFINANCE_PALMARES_URL,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def _post_sikafinance_palmares(self, variation="h", market="br", since="yesterday"):
        response = self.sikafinance_session.get(self.SIKAFINANCE_PALMARES_URL, timeout=self.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        token_input = soup.find("input", {"name": "__RequestVerificationToken"})
        token = token_input["value"] if token_input else ""

        form_data = {
            "__RequestVerificationToken": token,
            "dlMarket": market,
            "dlVariation": variation,
            "dlSince": since,
        }

        post_response = self.sikafinance_session.post(
            self.SIKAFINANCE_PALMARES_URL,
            data=form_data,
            timeout=self.timeout,
        )
        post_response.raise_for_status()
        return BeautifulSoup(post_response.text, "html.parser")

    def _parse_sikafinance_palmares_table(self, soup):
        table = soup.find("table", id="tabQuotes")
        if not table:
            return []

        rows = []
        for tr in table.select("tbody tr"):
            cells = tr.find_all("td")
            if len(cells) < 6:
                continue

            link = cells[0].find("a", href=True)
            href = (link["href"] if link else "").strip()
            code = None
            symbol = None
            if "cotation_" in href:
                code = href.split("cotation_", 1)[-1]
                symbol = code.split(".", 1)[0] if "." in code else code

            rows.append(
                {
                    "name": self._clean_text(cells[0].get_text(" ", strip=True)),
                    "high": self._parse_number(cells[1].get_text(" ", strip=True)),
                    "low": self._parse_number(cells[2].get_text(" ", strip=True)),
                    "last": self._parse_number(cells[3].get_text(" ", strip=True)),
                    "volume": self._parse_number(cells[4].get_text(" ", strip=True)),
                    "variation_pct": self._parse_percentage(
                        cells[5].get_text(" ", strip=True)
                    ),
                    "code": code,
                    "symbol": symbol,
                    "cotation_href": href,
                    "cotation_url": urljoin(self.SIKAFINANCE_PALMARES_URL, href)
                    if href
                    else None,
                }
            )

        return rows

    def fetch_sikafinance_company_profile(self, details_url):
        soup = self._get_sikafinance_soup(details_url)
        text = self._clean_text(soup.get_text(" ", strip=True)) or ""

        telephone = self._extract_between(text, "Téléphone :", "Fax :")
        fax = self._extract_between(text, "Fax :", "Adresse :")
        address = self._extract_between(text, "Adresse :", "Dirigeants :")
        governance_text = self._extract_sikafinance_governance_text(text)
        shareholders_text = self._extract_between(
            text, "Principaux actionnaires", "Les chiffres sont en millions de FCFA"
        ) or ""

        from analysis.governance_parser import enrich_governance

        governance_roles = self._parse_governance_roles(governance_text)
        governance = enrich_governance(
            {
                "source": "sikafinance",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "raw": governance_text,
                "roles": governance_roles,
                "chairman": self._pick_role_value(
                    governance_roles,
                    [
                        "PCA",
                        "Président directeur général",
                        "Président du Conseil d'Administration",
                        "Président du conseil d'administration",
                    ],
                ),
                "chief_executive": self._pick_role_value(
                    governance_roles,
                    [
                        "Directeur Général",
                        "Directeur general",
                        "PDG",
                        "DG",
                        "Direction Générale",
                        "Managing Director",
                    ],
                ),
            }
        )

        market_stats = self._parse_sikafinance_market_stats(text)
        financial_statements = self._parse_sikafinance_financial_table(soup)

        return {
            "source_url": details_url,
            "telephone": telephone,
            "fax": fax,
            "address": address,
            "governance": governance,
            "shareholders": self._parse_sikafinance_shareholders(shareholders_text),
            "market_stats": market_stats,
            "financial_statements": financial_statements,
        }

    def fetch_sikafinance_price_history(self, sikafinance_code, max_rows=None):
        """
        Historique quotidien réel (OHLCV) depuis /marches/historiques/{code}.
        Ex. code : ABJC.ci
        """
        if not sikafinance_code:
            return []

        code = str(sikafinance_code).strip()
        url = urljoin(self.SIKAFINANCE_QUOTES_URL, f"/marches/historiques/{code}")
        soup = self._get_sikafinance_soup(url)
        table = soup.find("table")
        if not table:
            return []

        rows = []
        table_rows = table.find_all("tr")
        if len(table_rows) < 2:
            return []

        for tr in table_rows[1:]:
            cells = [
                self._clean_text(cell.get_text(" ", strip=True))
                for cell in tr.find_all(["th", "td"])
            ]
            if len(cells) < 5:
                continue

            match = re.match(r"(\d{2})/(\d{2})/(\d{4})", cells[0] or "")
            if not match:
                continue

            day, month, year = match.groups()
            close = self._parse_number(cells[1])
            if close is None:
                continue

            rows.append(
                {
                    "date": f"{year}-{month}-{day}",
                    "close": close,
                    "low": self._parse_number(cells[2]),
                    "high": self._parse_number(cells[3]),
                    "open": self._parse_number(cells[4]),
                    "volume": self._parse_number(cells[5]) if len(cells) > 5 else None,
                    "variation_pct": self._parse_percentage(cells[7])
                    if len(cells) > 7
                    else None,
                }
            )

        rows.sort(key=lambda item: item["date"])
        if max_rows and len(rows) > max_rows:
            rows = rows[-max_rows:]
        return rows

    def match_report_reference(self, company, references):
        company_aliases = self._company_aliases(company)
        for reference in references:
            reference_aliases = self._text_aliases(
                reference.get("issuer"), reference.get("description")
            )
            if company_aliases & reference_aliases:
                return reference
        return self._best_fuzzy_match(
            company_aliases, references, ["issuer", "description"], threshold=0.92
        )

    def match_sikafinance_quote(self, company, quotes):
        company_aliases = self._company_aliases(company)
        for quote in quotes:
            if company_aliases & self._text_aliases(quote.get("name")):
                return quote
        return self._best_fuzzy_match(company_aliases, quotes, ["name"], threshold=0.9)

    def _best_fuzzy_match(self, company_aliases, candidates, fields, threshold=0.88):
        best_candidate = None
        best_ratio = 0.0

        for candidate in candidates:
            candidate_aliases = self._text_aliases(
                *[candidate.get(field) for field in fields if candidate.get(field)]
            )
            for company_alias in company_aliases:
                for candidate_alias in candidate_aliases:
                    ratio = SequenceMatcher(None, company_alias, candidate_alias).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_candidate = candidate

        if best_ratio >= threshold:
            return best_candidate
        return None

    def _deduplicate_companies(self, companies):
        deduplicated = []

        for company in sorted(companies, key=self._company_richness, reverse=True):
            existing = self._find_existing_company(
                deduplicated, self._company_aliases(company)
            )
            if existing:
                self._merge_company_records(existing, company)
            else:
                deduplicated.append(company)

        return deduplicated

    def _merge_company_records(self, target, source):
        for key, value in source.items():
            if value in (None, "", [], {}):
                continue

            if key not in target or target[key] in (None, "", [], {}):
                target[key] = value
                continue

            if isinstance(value, dict) and isinstance(target.get(key), dict):
                for child_key, child_value in value.items():
                    if child_value not in (None, "", [], {}):
                        target[key].setdefault(child_key, child_value)
                continue

            if isinstance(value, list) and isinstance(target.get(key), list):
                if len(value) > len(target[key]):
                    target[key] = value

    def _company_richness(self, company):
        return sum(
            1
            for key in [
                "symbol",
                "market_quote",
                "brvm_reports_reference",
                "financial_history",
                "shareholding",
                "board_members",
            ]
            if company.get(key)
        )

    def _find_existing_company(self, companies, aliases):
        for company in companies:
            if self._company_aliases(company) & aliases:
                return company

        best_company = None
        best_ratio = 0.0
        for company in companies:
            company_aliases = self._company_aliases(company)
            for left in company_aliases:
                for right in aliases:
                    ratio = SequenceMatcher(None, left, right).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_company = company

        if best_ratio >= 0.92:
            return best_company
        return None

    def _company_aliases(self, company):
        return self._text_aliases(
            company.get("display_name"),
            company.get("profile_name"),
            company.get("legal_name"),
            company.get("symbol"),
            company.get("brvm_reports_reference", {}).get("issuer"),
            company.get("brvm_reports_reference", {}).get("description"),
        )

    def _text_aliases(self, *values):
        aliases = set()
        country_replacements = {
            "CÔTE D'IVOIRE": "CI",
            "COTE D'IVOIRE": "CI",
            "COTE D IVOIRE": "CI",
            "BURKINA FASO": "BF",
            "BENIN": "BN",
            "MALI": "ML",
            "NIGER": "NG",
            "SENEGAL": "SN",
            "TOGO": "TG",
        }

        for value in values:
            if not value:
                continue

            cleaned = self._clean_text(value)
            in_parentheses = re.findall(r"\(([^)]*)\)", cleaned)
            abbreviated = cleaned
            for country, abbreviation in country_replacements.items():
                abbreviated = re.sub(country, abbreviation, abbreviated, flags=re.IGNORECASE)
            variants = {
                cleaned,
                re.sub(r"\([^)]*\)", " ", cleaned),
                cleaned.replace(" - ", " "),
                abbreviated,
            }
            variants.update(in_parentheses)

            for variant in variants:
                normalized = self._normalize_key(variant)
                if normalized:
                    aliases.add(normalized)

        return aliases

    def _extract_profile_website(self, soup):
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if href.startswith("http") and "brvm.org" not in href:
                return href
        return None

    def _parse_board_members(self, rows):
        if not rows or len(rows) < 2:
            return []

        members = []
        for row in rows[1:]:
            if len(row) < 2:
                continue
            members.append(
                {
                    "name": row[0],
                    "role": row[1] if len(row) > 1 else None,
                    "structure": row[2] if len(row) > 2 else None,
                }
            )
        return members

    def _parse_shareholding(self, rows):
        if not rows:
            return {"total_shares": None, "shareholders": []}

        total_shares = None
        shareholders = []

        for row in rows[1:]:
            if not row:
                continue

            first_cell = row[0]
            if "Nombre total d'actions" in first_cell:
                total_shares = {
                    "as_of": self._extract_date(first_cell),
                    "value": self._parse_number(row[1]) if len(row) > 1 else None,
                    "raw": row[1] if len(row) > 1 else None,
                }
                continue

            if first_cell.lower().startswith("actionnaires au"):
                continue

            if len(row) >= 2 and first_cell != "Actionnariat":
                shareholders.append(
                    {
                        "name": first_cell,
                        "percentage": self._parse_percentage(row[-1]),
                        "raw_percentage": row[-1],
                    }
                )

        return {"total_shares": total_shares, "shareholders": shareholders}

    def _parse_financial_history(self, rows):
        if not rows or len(rows) < 2:
            return []

        history = []
        for row in rows[1:]:
            if len(row) < 4:
                continue
            if not re.fullmatch(r"\d{4}", row[0]):
                continue
            history.append(
                {
                    "year": int(row[0]),
                    "revenue_mfcfa": self._parse_number(row[1]),
                    "net_income_mfcfa": self._parse_number(row[2]),
                    "net_dividend_per_share_fcfa": self._parse_number(row[3]),
                }
            )

        return history

    def _extract_labeled_value(self, paragraphs, label):
        for paragraph in paragraphs:
            if label in paragraph and ":" in paragraph:
                return paragraph.split(":", 1)[1].strip() or None
        return None

    def _attach_sikafinance_profile(self, company, quote_entry):
        details_url = quote_entry.get("details_url")
        if not details_url:
            return
        try:
            profile = self.fetch_sikafinance_company_profile(details_url)
            company["sikafinance_profile"] = profile
            company["sikafinance_governance"] = profile.get("governance")
        except Exception as exc:
            company["sikafinance_profile_error"] = str(exc)

    def _attach_brvm_balance_sheet(self, company, report_entry=None):
        """Extrait actif / dettes / capitaux propres depuis le dernier PDF BRVM."""
        if os.getenv("SCRAPE_BALANCE_SHEETS", "true").lower() in ("0", "false", "no"):
            return

        reference = report_entry or company.get("brvm_reports_reference") or {}
        report_page_url = reference.get("report_page_url")
        if not report_page_url:
            return

        if company.get("balance_sheet_history"):
            return

        try:
            symbol = company.get("symbol") or company.get("ticker")
            payload = self.fetch_balance_sheet_from_brvm(report_page_url, symbol=symbol)
            if payload:
                company["balance_sheet_history"] = payload.get("history") or []
                company["balance_sheet_meta"] = payload.get("meta") or {}
        except Exception as exc:
            company["balance_sheet_error"] = str(exc)

    def fetch_brvm_financial_pdf_links(self, report_page_url, limit=10):
        """Liste les PDF d'états financiers sur la fiche rapports BRVM."""
        page_url = report_page_url.rstrip("/")
        if "field_type_rapport_tid=" not in page_url:
            page_url = f"{page_url}?field_type_rapport_tid=57"

        from analysis.balance_sheet_parser import infer_report_year

        soup = self._get_brvm_soup(page_url)
        links = []
        seen = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href.lower().endswith(".pdf"):
                continue

            lowered = href.lower()
            if not any(
                token in lowered
                for token in (
                    "financier",
                    "financial",
                    "etats_financiers",
                    "etat_financier",
                    "etats-financiers",
                )
            ):
                continue

            full_url = urljoin(self.BRVM_BASE_URL, href)
            if full_url in seen:
                continue
            seen.add(full_url)

            title = self._clean_text(anchor.get_text(" ", strip=True)) or full_url
            links.append(
                {
                    "url": full_url,
                    "title": title,
                    "year": infer_report_year(pdf_url=full_url, pdf_title=title),
                }
            )

        return links[:limit]

    def fetch_balance_sheet_from_brvm(self, report_page_url, symbol=None, max_pdfs=4):
        """Télécharge et parse les états financiers BRVM (bilan)."""
        from analysis.balance_sheet_parser import (
            merge_balance_sheet_history,
            parse_balance_sheet_pdf,
        )

        links = self.fetch_brvm_financial_pdf_links(report_page_url)
        if not links:
            return None

        slug = report_page_url.rstrip("/").split("/")[-1].split("?")[0].lower()
        symbol_key = (symbol or slug).replace("-", "").replace(".", "").lower()[:12]

        links.sort(
            key=lambda item: (
                -(item.get("year") or 0),
                "synthese" not in item["url"].lower(),
                symbol_key not in item["url"].lower().replace("-", "").replace("_", ""),
            )
        )

        history = []
        meta = {"attempted_pdfs": 0, "successful_pdf": None, "report_page_url": report_page_url}

        for link in links[:max_pdfs]:
            meta["attempted_pdfs"] += 1
            try:
                response = self.brvm_session.get(
                    link["url"],
                    timeout=max(self.timeout, 45),
                    verify=self.verify_brvm_ssl,
                )
                response.raise_for_status()
                entries = parse_balance_sheet_pdf(
                    response.content,
                    pdf_url=link["url"],
                    pdf_title=link.get("title"),
                )
                if entries:
                    history = merge_balance_sheet_history(history, entries)
                    meta["successful_pdf"] = link["url"]
                    break
            except Exception:
                continue

        if not history:
            return None

        return {"history": history, "meta": meta}

    def _parse_sikafinance_market_stats(self, text):
        if not text:
            return None

        shares_match = re.search(
            r"Nombre de titres\s*:\s*([\d\s]+)",
            text,
            flags=re.IGNORECASE,
        )
        float_match = re.search(
            r"Flottant\s*:\s*([\d\s,\.]+)\s*%",
            text,
            flags=re.IGNORECASE,
        )
        cap_match = re.search(
            r"Valorisation de la soci[eé]t[eé]\s*:\s*([\d\s,\.]+)\s*MFCFA",
            text,
            flags=re.IGNORECASE,
        )

        if not shares_match and not float_match and not cap_match:
            return None

        return {
            "shares_outstanding": self._parse_number(shares_match.group(1))
            if shares_match
            else None,
            "float_pct": self._parse_percentage(float_match.group(1))
            if float_match
            else None,
            "market_cap_mfcfa": self._parse_number(cap_match.group(1)) if cap_match else None,
            "market_cap_raw": cap_match.group(0) if cap_match else None,
        }

    def _parse_sikafinance_financial_table(self, soup):
        row_keys = {
            "chiffre d affaires": "revenue_mfcfa",
            "chiffre d'affaires": "revenue_mfcfa",
            "croissance ca": "revenue_growth_pct",
            "resultat net": "net_income_mfcfa",
            "croissance rn": "net_income_growth_pct",
            "bnpa": "eps_fcfa",
            "per": "pe_ratio",
            "dividende": "dividend_per_share_fcfa",
        }

        for table in soup.find_all("table"):
            matrix = []
            for tr in table.find_all("tr"):
                cells = [
                    self._clean_text(cell.get_text(" ", strip=True))
                    for cell in tr.find_all(["th", "td"])
                ]
                if cells:
                    matrix.append(cells)

            if len(matrix) < 2:
                continue

            header = matrix[0]
            years = []
            for cell in header[1:]:
                if re.fullmatch(r"\d{4}", str(cell)):
                    years.append(int(cell))

            if not years:
                continue

            metric_rows = {}
            has_revenue = False
            for row in matrix[1:]:
                if not row:
                    continue
                label = self._normalize_financial_label(row[0])
                field = row_keys.get(label)
                if not field:
                    continue
                if field == "revenue_mfcfa":
                    has_revenue = True
                metric_rows[field] = row[1:]

            if not has_revenue:
                continue

            statements = []
            for index, year in enumerate(years):
                entry = {"year": year}
                for field, values in metric_rows.items():
                    if index >= len(values):
                        entry[field] = None
                        continue
                    raw = values[index]
                    if field in ("revenue_growth_pct", "net_income_growth_pct"):
                        entry[field] = self._parse_percentage(raw)
                    elif field == "pe_ratio":
                        parsed = self._parse_number(raw)
                        entry[field] = parsed
                    else:
                        entry[field] = self._parse_number(raw)
                statements.append(entry)

            if statements:
                return statements

        return []

    def _normalize_financial_label(self, label):
        if not label:
            return ""
        text = self._clean_text(label).lower()
        text = text.replace("’", "'").replace("'", "'")
        text = (
            text.replace("é", "e")
            .replace("è", "e")
            .replace("ê", "e")
            .replace("à", "a")
        )
        return re.sub(r"\s+", " ", text).strip()

    def _extract_sikafinance_governance_text(self, text):
        """Bloc dirigeants Sikafinance (tolère « Dirigeants » avec ou sans « : »)."""
        from analysis.governance_parser import normalize_governance_raw

        governance_text = (
            self._extract_between(text, "Dirigeants :", "Nombre de titres :")
            or self._extract_between(text, "Dirigeants:", "Nombre de titres :")
            or self._extract_between(text, "Dirigeants", "Nombre de titres :")
            or ""
        )
        return normalize_governance_raw(governance_text)

    def _extract_between(self, text, start_marker, end_marker):
        if not text:
            return None
        start = text.find(start_marker)
        if start < 0:
            return None
        start += len(start_marker)
        end = text.find(end_marker, start)
        if end < 0:
            end = len(text)
        value = self._clean_text(text[start:end])
        return value or None

    def _parse_governance_roles(self, raw_text):
        if not raw_text:
            return []

        labels = [
            "Président directeur général",
            "Président du Conseil d'Administration",
            "Président du conseil d'administration",
            "Direction Générale",
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
            "Directeur Reseau",
            "Directeur Service",
        ]

        pattern = r"(" + "|".join(re.escape(label) for label in labels) + r")\s*:\s*"
        matches = list(re.finditer(pattern, raw_text, flags=re.IGNORECASE))
        roles = []

        for index, match in enumerate(matches):
            role = self._clean_text(match.group(1))
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(raw_text)
            person = self._clean_text(raw_text[start:end])
            person = re.sub(r"\b(Nombre de titres|Flottant|Valorisation).*$", "", person or "", flags=re.IGNORECASE)
            person = self._clean_text(person)
            if person:
                roles.append({"role": role, "name": person})

        return roles

    def _pick_role_value(self, governance_roles, role_labels):
        wanted = {self._normalize_key(label) for label in role_labels}
        for entry in governance_roles:
            role_key = self._normalize_key(entry.get("role"))
            if role_key in wanted:
                return entry.get("name")
        return None

    def _parse_sikafinance_shareholders(self, raw_text):
        if not raw_text:
            return []
        shareholders = []
        for item in raw_text.split(";"):
            chunk = self._clean_text(item)
            if not chunk:
                continue
            if "*" in chunk:
                name, pct = chunk.split("*", 1)
                shareholders.append(
                    {
                        "name": self._clean_text(name),
                        "percentage": self._parse_percentage(pct),
                        "raw_percentage": self._clean_text(pct),
                    }
                )
            else:
                shareholders.append(
                    {
                        "name": chunk,
                        "percentage": None,
                        "raw_percentage": None,
                    }
                )
        return shareholders

    def _get_brvm_soup(self, url):
        response = self.brvm_session.get(
            url, timeout=self.timeout, verify=self.verify_brvm_ssl
        )
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def _get_sikafinance_soup(self, url):
        response = self.sikafinance_session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def _extract_table_rows(self, table):
        rows = []
        for tr in table.find_all("tr"):
            cells = [
                self._clean_text(cell.get_text(" ", strip=True))
                for cell in tr.find_all(["th", "td"])
            ]
            if cells:
                rows.append(cells)
        return rows

    def _find_table(self, tables, predicate):
        for table in tables:
            if predicate(table):
                return table
        return []

    def _find_brvm_node_link(self, block):
        for anchor in block.find_all("a", href=True):
            href = anchor["href"].strip()
            if href.startswith("/en/node/") or href.startswith("/fr/node/"):
                return href
        return None

    def _extract_directory_pagination_urls(self, soup):
        urls = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if href.startswith("/en/emetteurs/societes-cotees?page="):
                urls.append(urljoin(self.BRVM_BASE_URL, href))
        return urls

    def _extract_reports_pagination_urls(self, soup):
        urls = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if href.startswith("/en/rapports-societes-cotees?page="):
                urls.append(urljoin(self.BRVM_BASE_URL, href))
        return urls

    def _extract_external_link(self, block):
        for anchor in block.find_all("a", href=True):
            href = anchor["href"].strip()
            if href.startswith("http") and "brvm.org" not in href:
                return href
        return None

    def _extract_brvm_block_logo(self, block):
        """Extrait le logo affiché sur l'annuaire BRVM des sociétés cotées."""
        img = block.find("img")
        if not img:
            return None

        src = (img.get("src") or img.get("data-src") or "").strip()
        if not src:
            return None

        style_match = re.search(r"/files/styles/[^/]+/public/([^?\"']+)", src)
        if style_match:
            filename = style_match.group(1)
            if self._is_generic_brvm_logo(filename):
                return None
            return urljoin(self.BRVM_BASE_URL, f"/sites/default/files/{filename}")

        if "/sites/default/files/" in src:
            filename = src.split("/sites/default/files/")[-1].split("?")[0]
            if self._is_generic_brvm_logo(filename):
                return None
            return urljoin(self.BRVM_BASE_URL, f"/sites/default/files/{filename}")

        return None

    def _is_generic_brvm_logo(self, filename):
        lowered = (filename or "").lower()
        return "plan_de_travail" in lowered or lowered in {"logo.png", "logo-pi.png"}

    def fetch_brvm_logo_index(self):
        """Construit un index profile_url / nom → logo_url depuis l'annuaire BRVM."""
        index = {"by_profile_url": {}, "by_name": {}}
        for company in self.fetch_brvm_directory():
            logo_url = company.get("logo_url")
            if not logo_url:
                continue

            profile_url = company.get("brvm_profile_url")
            if profile_url:
                index["by_profile_url"][profile_url] = logo_url

            name_key = self._normalize_key(company.get("display_name"))
            if name_key:
                index["by_name"][name_key] = logo_url

        return index

    def _extract_email(self, text):
        match = re.search(r"[\w.\-+%]+@[\w.\-]+\.\w+", text)
        return match.group(0) if match else None

    def _extract_date(self, text):
        match = re.search(r"\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2}|\d{4}", text)
        return match.group(0) if match else None

    def _text_of(self, element):
        if not element:
            return None
        return element.get_text(" ", strip=True)

    def _clean_text(self, value):
        if value is None:
            return None
        return re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()

    def _normalize_key(self, value):
        text = self._clean_text(value)
        if not text:
            return None
        text = unicodedata.normalize("NFKD", text)
        text = "".join(char for char in text if not unicodedata.combining(char))
        text = text.upper()
        text = re.sub(r"[^A-Z0-9]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _parse_number(self, value):
        text = self._clean_text(value)
        if not text:
            return None

        text = text.replace("%", "").replace("FCFA", "").replace("XOF", "").strip()
        text = text.replace(" ", "")
        text = text.replace(",", ".")

        try:
            number = float(text)
        except ValueError:
            return None

        if number.is_integer():
            return int(number)
        return number

    def _parse_percentage(self, value):
        number = self._parse_number(value)
        if number is None:
            return None
        return float(number)

    def save_to_json(self, payload, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
