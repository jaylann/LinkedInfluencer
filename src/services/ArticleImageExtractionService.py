from typing import Optional

from pydantic import BaseModel


class ArticleImageExtractionService(BaseModel):
    @staticmethod
    def extract_techcrunch_image(text: str) -> Optional[str]:
        """Extract TechCrunch article image link from the given text."""
        try:
            return text.replace("\n", "").replace(" ", "").split(")**ImageCredits:**")[0].split("](")[-1].strip()
        except IndexError:
            return None

    @staticmethod
    def extract_arstechnica_image(text: str) -> Optional[str]:
        """Extract Ars Technica article image link from the given text."""
        try:
            return text.split("[Enlarge](")[1].split(")")[0].strip().replace("\n", "")
        except IndexError:
            return None
