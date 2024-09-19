import logging
from datetime import datetime
from typing import List, Optional
import random

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from pydantic import ValidationError

from src.models.RSSItem import RSSItem
from src.models.Post import Post

class DynamoDBService:
    """Service class for interacting with DynamoDB tables."""

    def __init__(self, region_name: str = 'eu-central-1'):
        """
        Initialize the DynamoDBService.

        Args:
            region_name (str): AWS region name. Defaults to 'eu-central-1'.
        """
        self.logger = logging.getLogger(__name__)
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.rss_table = self.dynamodb.Table('rss-feed-scraped-articles')
        self.posts_table = self.dynamodb.Table('linkedin-automation-posts')

    def save_rss_items(self, items: List[RSSItem]) -> None:
        """
        Save unique RSSItem objects to DynamoDB.

        Args:
            items (List[RSSItem]): List of RSSItem objects to save.
        """
        for item in items:
            try:
                if not self._item_exists(item.link):
                    self.rss_table.put_item(Item=item.model_dump())
                else:
                    self.logger.info(f"Item with link {item.link} already exists. Skipping.")
            except ClientError as e:
                self.logger.error(f"Error processing item with link {item.link}: {e.response['Error']['Message']}")
            except Exception as e:
                self.logger.error(f"Unexpected error processing item with link {item.link}: {str(e)}")

    def update_rss_item(self, item: RSSItem) -> None:
        """
        Update an existing RSSItem in DynamoDB.

        Args:
            item (RSSItem): RSSItem object to update.
        """
        try:
            self.rss_table.put_item(Item=item.model_dump())
        except ClientError as e:
            self.logger.error(f"Error updating item with link {item.link}: {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating item with link {item.link}: {str(e)}")

    def get_random_unprocessed_item(self) -> Optional[RSSItem]:
        """
        Retrieve a random unprocessed item from the DynamoDB table.

        Returns:
            Optional[RSSItem]: A random unprocessed RSSItem if available, None otherwise.
        """
        try:
            response = self.rss_table.query(
                IndexName='processed-id-index',
                KeyConditionExpression=Key('processed').eq(0),
                Limit=20
            )
            items = response.get('Items', [])

            if not items:
                self.logger.info("No unprocessed items found.")
                return None

            random_item = random.choice(items)
            if 'pub_date' in random_item:
                random_item['pub_date'] = datetime.fromisoformat(random_item['pub_date'])

            return RSSItem(**random_item)
        except ClientError as e:
            self.logger.error(f"ClientError querying DynamoDB: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        except ValidationError as e:
            self.logger.error(f"Error converting DynamoDB item to RSSItem: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")

        return None

    def get_last_unprocessed_rss_items(self, amount: int) -> List[RSSItem]:
        """
        Retrieve the last unprocessed RSSItems from the DynamoDB table.

        Args:
            amount (int): Number of items to retrieve.

        Returns:
            List[RSSItem]: List of unprocessed RSSItems.
        """
        try:
            response = self.rss_table.query(
                IndexName='processed-pub_date-index',
                KeyConditionExpression=Key('processed').eq(0),
                ScanIndexForward=False,
                Limit=amount
            )
            items = response.get('Items', [])

            if not items:
                self.logger.info("No unprocessed items found.")
                return []

            return [RSSItem(**item) for item in items]
        except ClientError as e:
            self.logger.error(f"ClientError querying DynamoDB: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        except ValidationError as e:
            self.logger.error(f"Error converting DynamoDB items to RSSItems: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")

        return []

    def get_latest_posts(self, amount: int) -> List[Post]:
        """
        Retrieve the latest posts from the LinkedIn automation posts table.

        Args:
            amount (int): Number of posts to retrieve.

        Returns:
            List[Post]: List of the latest Post objects.
        """
        try:
            response = self.posts_table.scan(
                Limit=amount,
                ProjectionExpression='id, post_time, title, content, tags, source_link'
            )
            items = response.get('Items', [])

            if not items:
                return []

            sorted_items = sorted(items, key=lambda x: x['post_time'], reverse=True)[:amount]
            return [Post.from_dynamodb_item(item) for item in sorted_items]
        except ClientError as e:
            self.logger.error(f"ClientError querying DynamoDB: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)

        return []

    def get_rss_items(self) -> List[RSSItem]:
        """
        Retrieve all RSSItem objects from DynamoDB.

        Returns:
            List[RSSItem]: List of all RSSItems in the table.
        """
        response = self.rss_table.scan()
        items = response.get('Items', [])
        return [RSSItem(**item) for item in items]

    def save_post(self, post: Post) -> None:
        """
        Save a Post object to DynamoDB.

        Args:
            post (Post): Post object to save.
        """
        self.posts_table.put_item(Item=post.model_dump())

    def _item_exists(self, link: str) -> bool:
        """
        Check if an item with the given link exists in the RSS table.

        Args:
            link (str): The link to check.

        Returns:
            bool: True if the item exists, False otherwise.
        """
        response = self.rss_table.query(
            IndexName='link-index',
            KeyConditionExpression='link = :link',
            ExpressionAttributeValues={':link': str(link)}
        )
        return response['Count'] > 0