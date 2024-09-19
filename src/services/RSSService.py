import xml.etree.ElementTree as ET
from typing import List

import requests
from pydantic import ValidationError

from src.models.RSSItem import RSSItem


class RSSService:
    """Service for fetching and parsing RSS feeds."""

    FEEDS = {
        'TechCrunch': 'https://techcrunch.com/feed/',
        'Ars Technica': 'https://arstechnica.com/information-technology/feed/'
    }

    @classmethod
    def fetch_feed(cls, outlet: str) -> List[RSSItem]:
        """
        Fetches and parses an RSS feed.

        Args:
            outlet (str): The name of the outlet to fetch the feed from.

        Returns:
            List[RSSItem]: A list of parsed RSS items.

        Raises:
            ValueError: If the outlet is not supported.
            requests.HTTPError: If the request to fetch the feed fails.
        """
        if outlet not in cls.FEEDS:
            raise ValueError(f"Unsupported outlet: {outlet}")

        response = requests.get(cls.FEEDS[outlet])
        response.raise_for_status()
        root = ET.fromstring(response.content)

        return [cls._parse_item(item, outlet) for item in root.findall('.//item')]

    @staticmethod
    def _parse_item(item: ET.Element, outlet: str) -> RSSItem:
        """
        Parses an XML item element into an RSSItem.

        Args:
            item (ET.Element): The XML element representing an RSS item.
            outlet (str): The name of the outlet.

        Returns:
            RSSItem: A parsed RSSItem object.
        """
        item_dict = {
            'title': item.findtext('title', ''),
            'link': item.findtext('link', ''),
            'creator': item.findtext('{http://purl.org/dc/elements/1.1/}creator'),
            'pub_date': item.findtext('pubDate'),
            'guid': item.findtext('guid', ''),
            'description': item.findtext('description', ''),
            'outlet': outlet,
            'categories': [cat.text for cat in item.findall('category') if cat.text]
        }

        try:
            return RSSItem(**item_dict)
        except ValidationError as e:
            # Log the error and return None, or handle it as appropriate for your use case
            print(f"Error parsing item from {outlet}: {e}")
            return None

    @classmethod
    def fetch_tech_crunch(cls) -> List[RSSItem]:
        """Fetches the TechCrunch RSS feed."""
        return cls.fetch_feed('TechCrunch')

    @classmethod
    def fetch_ars_technica(cls) -> List[RSSItem]:
        """Fetches the Ars Technica RSS feed."""
        return cls.fetch_feed('Ars Technica')
