import html
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from src.models.Post import Post

def remove_last_line_if_hashtag(text):
    # Split the input text into lines
    lines = text.splitlines()

    # Check if the last line contains a '#'
    if lines and '#' in lines[-1]:
        # Remove the last line
        lines.pop()

    # Join the lines back into a single string
    return '\n'.join(lines)

class S3Service:
    def __init__(self):
        self.s3 = boto3.client('s3')

    def update_rss_feed(self, bucket_name: str, key: str, post: Post) -> None:
        """Updates the RSS feed XML file on S3 with the new post at the top."""
        try:
            root = self._get_existing_rss(bucket_name, key)
        except ClientError:
            root = self._create_new_rss()

        channel = root.find('channel')
        self._update_last_build_date(channel)
        self._add_new_item(channel, post)

        rss_feed = ET.tostring(root, encoding='unicode', method='xml')
        self.s3.put_object(Bucket=bucket_name, Key=key, Body=rss_feed.encode('utf-8'), ContentType='application/rss+xml')

    def _get_existing_rss(self, bucket_name: str, key: str) -> ET.Element:
        obj = self.s3.get_object(Bucket=bucket_name, Key=key)
        rss_content = obj['Body'].read().decode('utf-8')
        parser = ET.XMLParser(encoding="utf-8")
        return ET.fromstring(rss_content, parser=parser)

    def _create_new_rss(self) -> ET.Element:
        root = ET.Element('rss', version='2.0')
        channel = ET.SubElement(root, 'channel')
        ET.SubElement(channel, 'title').text = 'Justin Lanfermann LinkedIn Feed'
        ET.SubElement(channel, 'link').text = 'https://www.linkedin.com/in/justin-lanfermann-07352124b/'
        ET.SubElement(channel, 'description').text = 'Here I post the most exciting pieces of news in the tech world!'
        ET.SubElement(channel, 'language').text = 'en-us'
        ET.SubElement(channel, 'pubDate').text = self._format_datetime(datetime.now(timezone.utc))
        return root

    def _update_last_build_date(self, channel: ET.Element) -> None:
        last_build_date = channel.find('lastBuildDate')
        if last_build_date is None:
            last_build_date = ET.SubElement(channel, 'lastBuildDate')
        last_build_date.text = self._format_datetime(datetime.now(timezone.utc))

    def _add_new_item(self, channel: ET.Element, post: Post) -> None:
        item = ET.Element('item')
        ET.SubElement(item, 'title').text = post.title
        ET.SubElement(item, 'link').text = str(post.source_link)
        ET.SubElement(item, 'image_link').text = str(post.image_link)
        content = remove_last_line_if_hashtag(post.content)
        source = 'TechCrunch' if 'techcrunch' in str(post.source_link).lower() else 'Ars Technica'
        description = f"{content}\n\nSource: {source}\n{' '.join([f'#{tag}' for tag in post.tags])}"
        ET.SubElement(item, 'description').text = description
        ET.SubElement(item, 'pubDate').text = self._format_datetime(datetime.now(timezone.utc))

        # Insert the new item at the beginning of the channel
        channel.insert(0, item)

    @staticmethod
    def _format_datetime(dt: datetime) -> str:
        return dt.strftime('%a, %d %b %Y %H:%M:%S %z')