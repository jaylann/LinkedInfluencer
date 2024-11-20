import logging
from typing import Optional

from pydantic import BaseModel

# Initialize the logger
logger = logging.getLogger("AppLogger")


# ==============================================================
# Similar to ArticleService. Check here if no image is found.
# Same thing for test cases here.
# ==============================================================

class ArticleImageExtractionService(BaseModel):
    @staticmethod
    def extract_techcrunch_image(text: str) -> Optional[str]:
        """Extract TechCrunch article image link from the given text."""
        logger.info("Starting extraction of TechCrunch image.")
        try:
            image = text.replace("\n", "").replace(" ", "").split(")**ImageCredits:**")[0].split("](")[-1].strip()
            logger.info("Successfully extracted TechCrunch image: %s", image)
            return image
        except IndexError:
            logger.warning("TechCrunch image not found in the provided text.")
            return None

    @staticmethod
    def extract_arstechnica_image(text: str) -> Optional[str]:
        """Extract Ars Technica article image link from the given text."""
        logger.info("Starting extraction of Ars Technica image.")
        try:
            image = text.split("[Enlarge](")[1].split(")")[0].strip().replace("\n", "")
            logger.info("Successfully extracted Ars Technica image: %s", image)
            return image
        except IndexError:
            logger.warning("Ars Technica image not found in the provided text.")
            return None
