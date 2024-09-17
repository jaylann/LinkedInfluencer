import xml.etree.ElementTree as ET
from typing import List

import requests

from src.models.RSSItem import RSSItem


class RSSService:
    TECH_CRUNCH_FEED_URL = 'https://techcrunch.com/feed/'
    ARS_TECHNICA_FEED_URL = 'https://arstechnica.com/information-technology/feed/'

    @staticmethod
    def fetch_tech_crunch() -> List[RSSItem]:
        """Fetches the RSS feed and returns a list of RSSItem objects."""
        response = requests.get(RSSService.TECH_CRUNCH_FEED_URL)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        items = []
        for item in root.findall('.//item'):
            item_dict = {}
            for child in item:
                tag = child.tag.split('}', 1)[-1]  # Handle namespaces
                if tag == 'category':
                    item_dict.setdefault('categories', []).append(child.text)
                else:
                    item_dict[tag] = child.text

            # Rename keys to match RSSItem field names
            item_dict['pub_date'] = item_dict.pop('pubDate', None)

            rss_item = RSSItem(**item_dict)
            items.append(rss_item)

        return items

    @staticmethod
    def fetch_ars_technica() -> List[RSSItem]:
        """Fetches the Ars Technica RSS feed and returns a list of RSSItem objects."""
        response = requests.get(RSSService.ARS_TECHNICA_FEED_URL)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        items = []
        for item in root.findall('.//item'):
            item_dict = {
                'title': item.findtext('title'),
                'link': item.findtext('link'),
                'creator': item.findtext('{http://purl.org/dc/elements/1.1/}creator'),
                'pub_date': item.findtext('pubDate'),
                'guid': item.findtext('guid'),
                'description': item.findtext('description'),
                'outlet': 'Ars Technica',
                'categories': [cat.text for cat in item.findall('category')]
            }

            rss_item = RSSItem(**item_dict)
            items.append(rss_item)

        return items
