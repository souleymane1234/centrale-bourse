"""Scrape des actualités publiées sur brvm.org."""

import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
import urllib3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR_DIR = os.path.join(BASE_DIR, ".vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)

from bs4 import BeautifulSoup

BRVM_BASE = "https://www.brvm.org"
NEWS_LIST_URL = f"{BRVM_BASE}/fr/actualites"
DEFAULT_OUTPUT = os.path.join(BASE_DIR, "data", "news_articles.json")


def _slugify(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:120] or "actualite"


class BRVMNewsScraper:
    def __init__(self, timeout=30, verify_ssl=False):
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "fr-FR,fr;q=0.9",
            }
        )
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def fetch_html(self, url):
        response = self.session.get(url, timeout=self.timeout, verify=self.verify_ssl)
        response.raise_for_status()
        return response.text

    def discover_article_links(self, html):
        soup = BeautifulSoup(html, "html.parser")
        links = []
        seen = set()

        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "").strip()
            if not href or href.startswith("#"):
                continue
            full = urljoin(BRVM_BASE, href)
            path = urlparse(full).path.lower()
            if "/actualites" not in path or path.rstrip("/") == "/fr/actualites":
                continue
            title = anchor.get_text(" ", strip=True)
            if len(title) < 15:
                continue
            if full in seen:
                continue
            seen.add(full)
            links.append({"url": full, "title_hint": title})

        return links[:40]

    def parse_article_page(self, url, title_hint=None):
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")

        title = None
        for selector in ("h1.page-title", "h1", "article h1"):
            node = soup.select_one(selector)
            if node:
                title = node.get_text(" ", strip=True)
                break
        if not title:
            title = title_hint or "Actualité BRVM"

        body_node = soup.select_one("article .field--name-body") or soup.select_one(
            "div.field-item, article .content, main .region-content"
        )
        paragraphs = []
        if body_node:
            for paragraph in body_node.select("p"):
                text = paragraph.get_text(" ", strip=True)
                if text:
                    paragraphs.append(text)
        excerpt = paragraphs[0][:280] if paragraphs else title[:280]
        body = "\n\n".join(paragraphs)

        image_url = None
        for img in soup.select("article img, .field--name-field-image img, img"):
            src = img.get("src") or img.get("data-src")
            if src and "logo" not in src.lower():
                image_url = urljoin(BRVM_BASE, src)
                break

        published = None
        time_node = soup.select_one("time[datetime]")
        if time_node and time_node.get("datetime"):
            published = time_node["datetime"]

        badge = "brvm"
        lower = f"{title} {excerpt}".lower()
        if "dividend" in lower:
            badge = "dividende"
        elif "obligation" in lower:
            badge = "obligation"
        elif "séance" in lower or "cotation" in lower or "marché" in lower:
            badge = "marche"

        return {
            "slug": _slugify(title),
            "title": title,
            "excerpt": excerpt,
            "body": body,
            "badge": badge,
            "media_type": "image" if image_url else None,
            "image_url": image_url,
            "video_url": None,
            "source": "BRVM",
            "source_url": url,
            "published_at": published or datetime.now(timezone.utc).isoformat(),
            "author": "BRVM",
        }

    def scrape(self, limit=20):
        listing_html = self.fetch_html(NEWS_LIST_URL)
        links = self.discover_article_links(listing_html)
        articles = []
        for entry in links[:limit]:
            try:
                articles.append(
                    self.parse_article_page(entry["url"], title_hint=entry.get("title_hint"))
                )
            except Exception as exc:
                print(f"⚠️  Article ignoré {entry['url']} : {exc}")
        return articles

    def save(self, articles, output_path=None):
        output_path = output_path or DEFAULT_OUTPUT
        existing = []
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as file:
                payload = json.load(file)
                existing = payload.get("articles") or []

        by_slug = {item.get("slug"): item for item in existing if item.get("slug")}
        for article in articles:
            by_slug[article["slug"]] = article

        merged = list(by_slug.values())
        merged.sort(key=lambda item: item.get("published_at") or "", reverse=True)

        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "brvm.org",
            "articles": merged,
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        return payload


def scrape_brvm_news(output_path=None, limit=20):
    scraper = BRVMNewsScraper(verify_ssl=False)
    articles = scraper.scrape(limit=limit)
    return scraper.save(articles, output_path=output_path)
