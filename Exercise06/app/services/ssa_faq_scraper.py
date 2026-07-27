from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class FAQDocument:
    question: str
    answer: str
    url: str


class SSAFAQScraper:
    def __init__(self, seed_url: str, timeout_seconds: int = 20) -> None:
        self.seed_url = seed_url
        self.timeout_seconds = timeout_seconds
        self._session = requests.Session()

    def collect_question_urls(self, max_list_pages: int = 15, max_question_pages: int = 500) -> list[str]:
        to_visit = [self.seed_url]
        visited: set[str] = set()
        question_urls: set[str] = set()

        while to_visit and len(visited) < max_list_pages and len(question_urls) < max_question_pages:
            current_url = to_visit.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)

            soup = self._fetch_soup(current_url)
            if soup is None:
                continue

            for href in self._extract_hrefs(soup):
                absolute_url = urljoin(current_url, href)
                if "/faqs/en/questions/" not in absolute_url:
                    continue

                if absolute_url.rstrip("/") == self.seed_url.rstrip("/"):
                    continue

                if absolute_url.endswith(".html"):
                    question_urls.add(absolute_url)
                    if len(question_urls) >= max_question_pages:
                        break
                else:
                    if absolute_url not in visited and absolute_url not in to_visit:
                        to_visit.append(absolute_url)

        return sorted(question_urls)

    def scrape_questions(self, urls: Iterable[str]) -> list[FAQDocument]:
        documents: list[FAQDocument] = []
        for url in urls:
            soup = self._fetch_soup(url)
            if soup is None:
                continue

            question = self._extract_question(soup)
            answer = self._extract_answer(soup)
            if not question or not answer:
                continue

            documents.append(FAQDocument(question=question, answer=answer, url=url))

        return documents

    def _fetch_soup(self, url: str) -> BeautifulSoup | None:
        try:
            response = self._session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException:
            return None

    @staticmethod
    def _extract_hrefs(soup: BeautifulSoup) -> list[str]:
        hrefs: list[str] = []
        for anchor in soup.select("a[href]"):
            href = anchor.get("href")
            if href:
                hrefs.append(href)
        return hrefs

    @staticmethod
    def _extract_question(soup: BeautifulSoup) -> str:
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(" ", strip=True)

        title = soup.find("title")
        return title.get_text(" ", strip=True) if title else ""

    @staticmethod
    def _extract_answer(soup: BeautifulSoup) -> str:
        candidate_containers = [
            soup.find("main"),
            soup.find("article"),
            soup.find(id="content"),
            soup.find(class_="faq-body"),
            soup,
        ]

        for container in candidate_containers:
            if container is None:
                continue

            parts: list[str] = []
            for element in container.select("p, li"):
                text = element.get_text(" ", strip=True)
                if len(text) >= 20:
                    parts.append(text)

            if parts:
                seen: set[str] = set()
                deduped = [part for part in parts if not (part in seen or seen.add(part))]
                return "\n".join(deduped)

        return ""
