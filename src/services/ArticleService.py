import re
from typing import Optional

import html2text
import requests
from pydantic import BaseModel


class ArticleImageExtractor(BaseModel):

    @staticmethod
    def extract_techcrunch_article_image(text: str) -> Optional[str]:
        """
        Extracts the TechCrunch article image link from the given text.

        Args:
            text (str): The input text containing the link to be extracted.

        Returns:
            Optional[str]: The extracted link or None if not found.
        """
        return text.replace("\n", "").replace(" ", "").split(")**ImageCredits:**")[0].split("![](")[-1].strip().replace("\n", "")

    @staticmethod
    def extract_arstechnica_article_image(text: str) -> Optional[str]:
        """
        Extracts the TechCrunch article image link from the given text.

        Args:
            text (str): The input text containing the link to be extracted.

        Returns:
            Optional[str]: The extracted link or None if not found.
        """
        return text.split("[Enlarge](")[1].split(")")[0].strip().replace("\n", "")



class ArticleService:
    @staticmethod
    def extract_article_text_tech_crunch(url: str) -> str:
        """Extracts article text from a given URL."""
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text

        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = True
        article_text = text_maker.handle(html_content)
        text_maker.ignore_links = False
        links = text_maker.handle(html_content)
        with open("test.txt", "w") as f:
            f.write(links)

        image_link = ArticleImageExtractor.extract_techcrunch_article_image(links)


        start_marker = "#"
        end_marker = "### More TechCrunch"
        start_pos = article_text.find(start_marker)
        if start_pos == -1:
            raise ValueError("Start marker not found.")
        start_pos += len(start_marker)
        end_pos = article_text.find(end_marker, start_pos)
        if end_pos == -1:
            raise ValueError("End marker not found.")
        extracted_text = article_text[start_pos:end_pos].strip()
        return extracted_text, image_link

    @staticmethod
    def extract_article_text_ars_technica(url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text

        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = True
        article_text = text_maker.handle(html_content)
        text_maker.ignore_links = False
        links = text_maker.handle(html_content)

        image_link = ArticleImageExtractor.extract_arstechnica_article_image(links)

        start_marker = "####"
        end_marker = "### Channel Ars Technica"
        start_pos = article_text.find(start_marker)
        if start_pos == -1:
            raise ValueError("Start marker not found.")
        start_pos += len(start_marker)
        end_pos = article_text.find(end_marker, start_pos)
        if end_pos == -1:
            raise ValueError("End marker not found.")
        extracted_text = article_text[start_pos:end_pos].strip()
        return extracted_text, image_link

