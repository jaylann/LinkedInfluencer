import xml.etree.ElementTree as ET
from typing import List

import requests
from pydantic import ValidationError

from src.models.RSSItem import RSSItem
import logging


class RSSService:
    """Service for fetching and parsing RSS feeds."""

    # Initialize a class-level logger
    logger = logging.getLogger("AppLogger")

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
        cls.logger.info(f"Starting fetch for outlet: {outlet}")

        if outlet not in cls.FEEDS:
            cls.logger.error(f"Unsupported outlet: {outlet}")
            raise ValueError(f"Unsupported outlet: {outlet}")

        url = cls.FEEDS[outlet]
        cls.logger.debug(f"Fetching URL: {url}")

        try:
            response = requests.get(url)
            response.raise_for_status()
            cls.logger.debug(f"Successfully fetched data from {url}")
        except requests.HTTPError as e:
            cls.logger.error(f"HTTP error while fetching {outlet} feed: {e}")
            raise

        try:
            root = ET.fromstring(response.content)
            cls.logger.debug(f"XML content parsed successfully for {outlet}")
        except ET.ParseError as e:
            cls.logger.error(f"Error parsing XML for {outlet}: {e}")
            raise

        items = root.findall('.//item')
        cls.logger.info(f"Found {len(items)} items in {outlet} feed")

        parsed_items = []
        for item in items:
            rss_item = cls._parse_item(item, outlet)
            if rss_item:
                parsed_items.append(rss_item)

        cls.logger.info(f"Successfully parsed {len(parsed_items)} items for {outlet} feed")
        return parsed_items

    @classmethod
    def _parse_item(cls, item: ET.Element, outlet: str) -> RSSItem:
        """
        Parses an XML item element into an RSSItem.

        Args:
            item (ET.Element): The XML element representing an RSS item.
            outlet (str): The name of the outlet.

        Returns:
            RSSItem: A parsed RSSItem object, or None if validation fails.
        """
        item_dict = {
            'title': item.findtext('title', '').strip(),
            'link': item.findtext('link', '').strip(),
            'creator': item.findtext('{http://purl.org/dc/elements/1.1/}creator', '').strip(),
            'pub_date': item.findtext('pubDate', '').strip(),
            'guid': item.findtext('guid', '').strip(),
            'description': item.findtext('description', '').strip(),
            'outlet': outlet,
            'categories': [cat.text.strip() for cat in item.findall('category') if cat.text]
        }

        try:
            rss_item = RSSItem(**item_dict)
            cls.logger.debug(f"Parsed RSS item: {rss_item.title}")
            return rss_item
        except ValidationError as e:
            cls.logger.warning(f"Validation error parsing item from {outlet}: {e}")
            return None

    @classmethod
    def fetch_tech_crunch(cls) -> List[RSSItem]:
        """Fetches the TechCrunch RSS feed."""
        cls.logger.info("Fetching TechCrunch feed")
        return cls.fetch_feed('TechCrunch')

    @classmethod
    def fetch_ars_technica(cls) -> List[RSSItem]:
        """Fetches the Ars Technica RSS feed."""
        cls.logger.info("Fetching Ars Technica feed")
        return cls.fetch_feed('Ars Technica')
