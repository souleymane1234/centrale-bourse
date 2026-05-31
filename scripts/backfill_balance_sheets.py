#!/usr/bin/env python3
"""Remplit balance_sheet_history dans data/companies_full.json via les PDF BRVM."""

import json
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from collectors.company_info_scraper import CompanyInfoScraper

COMPANIES_PATH = os.path.join(BASE_DIR, "data", "companies_full.json")
DELAY = float(os.getenv("BALANCE_SHEET_FETCH_DELAY", "0.35"))


def main():
    with open(COMPANIES_PATH, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    scraper = CompanyInfoScraper()
    updated = 0
    skipped = 0
    failed = 0

    for company in payload.get("companies", []):
        reference = company.get("brvm_reports_reference") or {}
        report_url = reference.get("report_page_url")
        name = company.get("display_name") or company.get("profile_name") or "?"

        if not report_url:
            skipped += 1
            continue

        if company.get("balance_sheet_history"):
            skipped += 1
            continue

        try:
            result = scraper.fetch_balance_sheet_from_brvm(report_url)
            if result:
                company["balance_sheet_history"] = result["history"]
                company["balance_sheet_meta"] = result["meta"]
                updated += 1
                latest = result["history"][0]
                print(
                    f"✅ {name}: actif={latest.get('total_assets_mfcfa')} "
                    f"CP={latest.get('equity_mfcfa')} dettes={latest.get('debt_mfcfa')}"
                )
            else:
                failed += 1
                print(f"⚠️  {name}: bilan non extrait")
        except Exception as exc:
            failed += 1
            print(f"❌ {name}: {exc}")

        time.sleep(DELAY)

    with open(COMPANIES_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    print(f"\nTerminé — mis à jour: {updated}, ignorés: {skipped}, échecs: {failed}")


if __name__ == "__main__":
    main()
