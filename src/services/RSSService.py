import xml.etree.ElementTree as ET
from typing import List

import requests

from src.models.RSSItem import RSSItem


class RSSService:
    FEED_URL = 'https://techcrunch.com/feed/'

    @staticmethod
    def fetch_feed() -> List[RSSItem]:
        """Fetches the RSS feed and returns a list of RSSItem objects."""
        response = requests.get(RSSService.FEED_URL)
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
