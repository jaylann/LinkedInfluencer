from typing import Optional, Tuple

import html2text
import requests
from pydantic import HttpUrl

from src.services.ArticleImageExtractionService import ArticleImageExtractionService


class ArticleService:
    @staticmethod
    def _fetch_and_parse_html(url: HttpUrl) -> Tuple[str, str]:
        """Fetch HTML content and parse it to plain text and links."""
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text

        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = True
        article_text = text_maker.handle(html_content)

        text_maker.ignore_links = False
        links = text_maker.handle(html_content)

        return article_text, links

    @staticmethod
    def _extract_text_between_markers(text: str, start_marker: str, end_marker: str) -> str:
        """Extract text between given start and end markers."""
        start_pos = text.find(start_marker)
        if start_pos == -1:
            raise ValueError(f"Start marker '{start_marker}' not found.")
        start_pos += len(start_marker)

        end_pos = text.find(end_marker, start_pos)
        if end_pos == -1:
            raise ValueError(f"End marker '{end_marker}' not found.")

        return text[start_pos:end_pos].strip()

    @classmethod
    def extract_techcrunch_article(cls, url: HttpUrl) -> Tuple[str, Optional[str]]:
        """Extract article text and image link from TechCrunch URL."""
        article_text, links = cls._fetch_and_parse_html(url)
        print(article_text)
        try:
            extracted_text = cls._extract_text_between_markers(article_text, "#", "## Most Popular")
        except ValueError:
            try:
                extracted_text = cls._extract_text_between_markers(article_text, "#", "![Author Avatar]")
            except ValueError:
                extracted_text = cls._extract_text_between_markers(article_text, "#", "## Related")
        image_link = ArticleImageExtractionService.extract_techcrunch_image(links)
        return extracted_text, image_link

    @classmethod
    def extract_arstechnica_article(cls, url: HttpUrl) -> Tuple[str, Optional[str]]:
        """Extract article text and image link from Ars Technica URL."""
        article_text, links = cls._fetch_and_parse_html(url)
        extracted_text = cls._extract_text_between_markers(article_text, "####", "### Channel Ars Technica")
        image_link = ArticleImageExtractionService.extract_arstechnica_image(links)
        return extracted_text, image_link
