import logging
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

import boto3
from botocore.exceptions import ClientError

from src.models.Post import Post
from src.models.RSSFeed import RSSFeed


class S3Service:
    """Service for interacting with AWS S3 and managing RSS feeds."""

    def __init__(self):
        self.s3 = boto3.client('s3')
        self.logger = logging.getLogger("AppLogger")
        self.logger.debug("S3Service initialized with AWS S3 client.")

    def update_rss_feed(self, bucket_name: str, key: str, post: Post) -> None:
        """
        Updates the RSS feed XML file on S3 with the new post at the top.

        Args:
            bucket_name (str): The name of the S3 bucket.
            key (str): The key of the RSS feed file in S3.
            post (Post): The new post to add to the RSS feed.
        """
        self.logger.info(f"Starting RSS feed update for bucket '{bucket_name}', key '{key}'.")
        try:
            root = self._get_existing_rss(bucket_name, key)
            self.logger.debug("Existing RSS feed retrieved successfully.")
        except ClientError as e:
            self.logger.warning(f"Failed to retrieve existing RSS feed: {e}. Creating a new RSS feed.")
            root = self._create_new_rss()
            self.logger.debug("New RSS feed created.")

        channel = root.find('channel')
        if channel is not None:
            self.logger.debug("Channel element found in RSS feed.")
        else:
            self.logger.error("Channel element not found in RSS feed.")
            raise ValueError("Invalid RSS feed structure: 'channel' element is missing.")

        self._update_last_build_date(channel)
        self.logger.info("Updated lastBuildDate in RSS feed.")

        self._add_new_item(channel, post)
        self.logger.info(f"Added new post titled '{post.title}' to RSS feed.")

        rss_feed = ET.tostring(root, encoding='unicode', method='xml')
        try:
            self.s3.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=rss_feed.encode('utf-8'),
                ContentType='application/rss+xml'
            )
            self.logger.info(f"RSS feed successfully updated in S3 at '{bucket_name}/{key}'.")
        except ClientError as e:
            self.logger.error(f"Failed to upload updated RSS feed to S3: {e}.")
            raise

    def _get_existing_rss(self, bucket_name: str, key: str) -> ET.Element:
        """Retrieves and parses the existing RSS feed from S3."""
        self.logger.debug(f"Fetching existing RSS feed from S3 bucket '{bucket_name}', key '{key}'.")
        obj = self.s3.get_object(Bucket=bucket_name, Key=key)
        rss_content = obj['Body'].read().decode('utf-8')
        parser = ET.XMLParser(encoding="utf-8")
        root = ET.fromstring(rss_content, parser=parser)
        self.logger.debug("Existing RSS feed parsed successfully.")
        return root

    def _create_new_rss(self) -> ET.Element:
        """Creates a new RSS feed structure."""
        self.logger.debug("Creating a new RSS feed structure.")
        rss_feed = RSSFeed()
        root = ET.Element('rss', version='2.0')
        channel = ET.SubElement(root, 'channel')

        for field, value in rss_feed.model_dump().items():
            ET.SubElement(channel, field).text = value
            self.logger.debug(f"Added '{field}' to channel with value '{value}'.")

        pub_date = self._format_datetime(datetime.now(timezone.utc))
        ET.SubElement(channel, 'pubDate').text = pub_date
        self.logger.debug(f"Set 'pubDate' to '{pub_date}' in new RSS feed.")
        return root

    def _update_last_build_date(self, channel: ET.Element) -> None:
        """Updates the lastBuildDate element in the RSS feed."""
        self.logger.debug("Updating 'lastBuildDate' in RSS feed.")
        last_build_date = channel.find('lastBuildDate')
        formatted_date = self._format_datetime(datetime.now(timezone.utc))
        if last_build_date is None:
            ET.SubElement(channel, 'lastBuildDate').text = formatted_date
            self.logger.debug("'lastBuildDate' element created and set.")
        else:
            last_build_date.text = formatted_date
            self.logger.debug("'lastBuildDate' element updated.")

    def _add_new_item(self, channel: ET.Element, post: Post) -> None:
        """Adds a new item to the RSS feed based on the provided post."""
        self.logger.debug(f"Adding new item for post titled '{post.title}'.")
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
        self.logger.debug(f"New item for post titled '{post.title}' inserted at the top of the channel.")

    @staticmethod
    def _remove_last_line_if_hashtag(text: str) -> str:
        """Removes the last line of the text if it contains a hashtag."""
        lines = text.splitlines()
        if lines and '#' in lines[-1]:
            logging.debug("Last line contains a hashtag and will be removed.")
            return '\n'.join(lines[:-1])
        return text

    @staticmethod
    def _format_datetime(dt: datetime) -> str:
        """Formats a datetime object to a string suitable for RSS feeds."""
        return dt.strftime('%a, %d %b %Y %H:%M:%S %z')
