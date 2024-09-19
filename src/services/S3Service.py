from datetime import datetime, timezone
from xml.etree import ElementTree as ET

import boto3
from botocore.exceptions import ClientError

from src.models.Post import Post


class S3Service:
    """Service for interacting with AWS S3 and managing RSS feeds."""

    def __init__(self):
        self.s3 = boto3.client('s3')

    def update_rss_feed(self, bucket_name: str, key: str, post: Post) -> None:
        """
        Updates the RSS feed XML file on S3 with the new post at the top.

        Args:
            bucket_name (str): The name of the S3 bucket.
            key (str): The key of the RSS feed file in S3.
            post (Post): The new post to add to the RSS feed.
        """
        try:
            root = self._get_existing_rss(bucket_name, key)
        except ClientError:
            root = self._create_new_rss()

        channel = root.find('channel')
        self._update_last_build_date(channel)
        self._add_new_item(channel, post)

        rss_feed = ET.tostring(root, encoding='unicode', method='xml')
        self.s3.put_object(Bucket=bucket_name, Key=key, Body=rss_feed.encode('utf-8'),
                           ContentType='application/rss+xml')

    def _get_existing_rss(self, bucket_name: str, key: str) -> ET.Element:
        """Retrieves and parses the existing RSS feed from S3."""
        obj = self.s3.get_object(Bucket=bucket_name, Key=key)
        rss_content = obj['Body'].read().decode('utf-8')
        parser = ET.XMLParser(encoding="utf-8")
        return ET.fromstring(rss_content, parser=parser)

    def _create_new_rss(self) -> ET.Element:
        """Creates a new RSS feed structure."""
        rss_feed = RSSFeed()
        root = ET.Element('rss', version='2.0')
        channel = ET.SubElement(root, 'channel')

        for field, value in rss_feed.model_dump().items():
            ET.SubElement(channel, field).text = value

        ET.SubElement(channel, 'pubDate').text = self._format_datetime(datetime.now(timezone.utc))
        return root

    def _update_last_build_date(self, channel: ET.Element) -> None:
        """Updates the lastBuildDate element in the RSS feed."""
        last_build_date = channel.find('lastBuildDate')
        if last_build_date is None:
            last_build_date = ET.SubElement(channel, 'lastBuildDate')
        last_build_date.text = self._format_datetime(datetime.now(timezone.utc))

    def _add_new_item(self, channel: ET.Element, post: Post) -> None:
        """Adds a new item to the RSS feed based on the provided post."""
        item = ET.Element('item')
        ET.SubElement(item, 'title').text = post.title
        ET.SubElement(item, 'link').text = str(post.source_link)
        ET.SubElement(item, 'image_link').text = str(post.image_link)

        content = self._remove_last_line_if_hashtag(post.content)
        source = 'TechCrunch' if 'techcrunch' in str(post.source_link).lower() else 'Ars Technica'
        description = f"{content}\n\nSource: {source}\n{' '.join([f'#{tag}' for tag in post.tags])}"
        ET.SubElement(item, 'description').text = description
        ET.SubElement(item, 'pubDate').text = self._format_datetime(datetime.now(timezone.utc))

        channel.insert(0, item)

    @staticmethod
    def _remove_last_line_if_hashtag(text: str) -> str:
        """Removes the last line of the text if it contains a hashtag."""
        lines = text.splitlines()
        return '\n'.join(lines[:-1] if lines and '#' in lines[-1] else lines)

    @staticmethod
    def _format_datetime(dt: datetime) -> str:
        """Formats a datetime object to a string suitable for RSS feeds."""
        return dt.strftime('%a, %d %b %Y %H:%M:%S %z')
