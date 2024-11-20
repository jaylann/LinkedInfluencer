from typing import Optional, Tuple

import html2text
import requests
from pydantic import HttpUrl

from src.services.ArticleImageExtractionService import ArticleImageExtractionService
import logging

# Initialize logger
logger = logging.getLogger("AppLogger")

#==============================================================
# IF ANYTHING BREAKS THIS IS THE CLASS TO CHECK FIRST.
# Because with the current method we just use a form of "Delimiters".
# Basically a string that always appears around the start and end of the article.
# However the sites may change these leading to our program just reading empty articles or crashing.
# TODO: Implement tests to check for validty of our delimiters using predefined cases.
#==============================================================


class ArticleService:
    @staticmethod
    def _fetch_and_parse_html(url: HttpUrl) -> Tuple[str, str]:
        """Fetch HTML content and parse it to plain text and links."""
        logger.info(f"Fetching HTML content from URL: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            logger.debug(f"Successfully fetched content from {url}")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch content from {url}: {e}")
            raise

        html_content = response.text

        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = True
        logger.debug("Parsing HTML content to extract article text.")
        article_text = text_maker.handle(html_content)

        text_maker.ignore_links = False
        logger.debug("Parsing HTML content to extract links.")
        links = text_maker.handle(html_content)

        return article_text, links

    @staticmethod
    def _extract_text_between_markers(text: str, start_marker: str, end_marker: str) -> str:
        """Extract text between given start and end markers."""
        logger.debug(f"Extracting text between markers: '{start_marker}' and '{end_marker}'")
        start_pos = text.find(start_marker)
        if start_pos == -1:
            logger.error(f"Start marker '{start_marker}' not found.")
            raise ValueError(f"Start marker '{start_marker}' not found.")
        start_pos += len(start_marker)

        end_pos = text.find(end_marker, start_pos)
        if end_pos == -1:
            logger.error(f"End marker '{end_marker}' not found.")
            raise ValueError(f"End marker '{end_marker}' not found.")

        extracted = text[start_pos:end_pos].strip()
        logger.debug("Successfully extracted text between markers.")
        return extracted

    @classmethod
    def extract_techcrunch_article(cls, url: HttpUrl) -> Tuple[str, Optional[str]]:
        """Extract article text and image link from TechCrunch URL."""
        logger.info(f"Extracting TechCrunch article from URL: {url}")
        try:
            article_text, links = cls._fetch_and_parse_html(url)
            logger.debug("Fetched and parsed HTML content successfully.")
        except Exception as e:
            logger.error(f"Error fetching and parsing HTML for TechCrunch article: {e}")
            raise

        try:
            extracted_text = cls._extract_text_between_markers(article_text, "#", "## Most Popular")
            logger.debug("Extracted text using markers '#', '## Most Popular'.")
        except ValueError as ve1:
            logger.warning(ve1)
            try:
                extracted_text = cls._extract_text_between_markers(article_text, "#", "![Author Avatar]")
                logger.debug("Extracted text using markers '#', '![Author Avatar]'.")
            except ValueError as ve2:
                logger.warning(ve2)
                try:
                    extracted_text = cls._extract_text_between_markers(article_text, "#", "## Related")
                    logger.debug("Extracted text using markers '#', '## Related'.")
                except ValueError as ve3:
                    logger.error("Failed to extract article text with all marker options.")
                    raise ve3

        image_link = ArticleImageExtractionService.extract_techcrunch_image(links)
        if image_link:
            logger.info(f"Extracted image link: {image_link}")
        else:
            logger.warning("No image link found for TechCrunch article.")

        return extracted_text, image_link

    @classmethod
    def extract_arstechnica_article(cls, url: HttpUrl) -> Tuple[str, Optional[str]]:
        """Extract article text and image link from Ars Technica URL."""
        logger.info(f"Extracting Ars Technica article from URL: {url}")
        try:
            article_text, links = cls._fetch_and_parse_html(url)
            logger.debug("Fetched and parsed HTML content successfully.")
        except Exception as e:
            logger.error(f"Error fetching and parsing HTML for Ars Technica article: {e}")
            raise

        try:
            extracted_text = cls._extract_text_between_markers(article_text, "####", "### Channel Ars Technica")
            logger.debug("Extracted text using markers '####', '### Channel Ars Technica'.")
        except ValueError as ve:
            logger.error(f"Failed to extract Ars Technica article text: {ve}")
            raise

        image_link = ArticleImageExtractionService.extract_arstechnica_image(links)
        if image_link:
            logger.info(f"Extracted image link: {image_link}")
        else:
            logger.warning("No image link found for Ars Technica article.")

        return extracted_text, image_link
