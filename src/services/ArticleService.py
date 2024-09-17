import html2text
import requests


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
        return extracted_text

    @staticmethod
    def extract_article_text_ars_technica(url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text

        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = True
        article_text = text_maker.handle(html_content)
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
        return extracted_text

print(ArticleService.extract_article_text_ars_technica("https://arstechnica.com/?p=2047618"))

