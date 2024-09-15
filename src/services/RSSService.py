import uuid
from typing import List, Optional
from datetime import datetime
import requests
import boto3
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field, HttpUrl, validator, field_validator
import html2text
import openai

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
                # Handle namespaces
                if '}' in child.tag:
                    tag = child.tag.split('}', 1)[1]
                else:
                    tag = child.tag
                if tag == 'category':
                    item_dict.setdefault('category', []).append(child.text)
                else:
                    item_dict[tag] = child.text
            rss_item = RSSItem(**item_dict)
            items.append(rss_item)
        return items