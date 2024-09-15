import uuid
from typing import List, Optional
from datetime import datetime
import requests
import boto3
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field, HttpUrl, validator, field_validator
import html2text
import openai

from src.models import RSSItem


class DynamoDBService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')

    def save_rss_items(self, items: List[RSSItem]):
        """Saves a list of RSSItem objects to DynamoDB."""
        table = self.dynamodb.Table('rss-feed-scraped-articles')
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item.model_dump())

    def get_rss_items(self) -> List[RSSItem]:
        """Retrieves all RSSItem objects from DynamoDB."""
        table = self.dynamodb.Table('rss-feed-scraped-articles')
        response = table.scan()
        items = response.get('Items', [])
        return [RSSItem(**item) for item in items]

    def save_post(self, post: Post):
        """Saves a Post object to DynamoDB."""
        table = self.dynamodb.Table('Posts')
        table.put_item(Item=post.model_dump())
