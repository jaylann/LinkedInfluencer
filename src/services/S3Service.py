import uuid
from typing import List, Optional
from datetime import datetime
import requests
import boto3
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field, HttpUrl, validator, field_validator
import html2text
import openai


class S3Service:
    def __init__(self):
        self.s3 = boto3.client('s3')

    def update_rss_feed(self, bucket_name: str, key: str, post: Post):
        """Updates the RSS feed XML file on S3 with the new post."""
        try:
            obj = self.s3.get_object(Bucket=bucket_name, Key=key)
            rss_content = obj['Body'].read()
            root = ET.fromstring(rss_content)
        except self.s3.exceptions.NoSuchKey:
            root = ET.Element('rss', version='2.0')
            channel = ET.SubElement(root, 'channel')
        else:
            channel = root.find('channel')

        # Create new item
        item = ET.SubElement(channel, 'item')
        title = ET.SubElement(item, 'title')
        title.text = post.content[:50]  # Assuming title is first 50 chars
        link = ET.SubElement(item, 'link')
        link.text = post.source_link
        description = ET.SubElement(item, 'description')
        description.text = post.content

        # Convert tree back to XML
        rss_feed = ET.tostring(root, encoding='utf-8', method='xml')

        # Upload back to S3
        self.s3.put_object(Bucket=bucket_name, Key=key, Body=rss_feed, ContentType='application/rss+xml')
