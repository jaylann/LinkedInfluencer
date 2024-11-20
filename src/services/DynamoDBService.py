import logging
import os
import random
from datetime import datetime
from typing import List, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from pydantic import ValidationError

from src.models.Post import Post
from src.models.RSSItem import RSSItem


class DynamoDBService:
    """Service class for interacting with DynamoDB tables."""

    # Default is what you set in .env. If your db isn't found you're probably not passing the correct region
    def __init__(self, region_name: str = os.getenv("AWS_REGION", "eu-central-1")):
        """
        Initialize the DynamoDBService.

        Args:
            region_name (str): AWS region name. Defaults to what you specified in .env.
        """
        self.logger = logging.getLogger("AppLogger")
        self.logger.debug(f"Initializing DynamoDBService with region: {region_name}")
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        try:
            self.rss_table = self.dynamodb.Table(os.getenv("DYNAMODB_SCRAPED_TABLE_NAME"))
            self.logger.info(f"Initialized RSS table: {os.getenv('DYNAMODB_SCRAPED_TABLE_NAME')}")
        except ClientError as e:
            self.logger.error(f"Error initializing RSS table: {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"Unexpected error initializing RSS table: {str(e)}")
        try:
            self.posts_table = self.dynamodb.Table(os.getenv("DYNAMODB_POSTS_TABLE_NAME"))
            self.logger.info(f"Initialized Posts table: {os.getenv('DYNAMODB_POSTS_TABLE_NAME')}")
        except ClientError as e:
            self.logger.error(f"Error initializing posts table: {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"Unexpected error initializing posts table: {str(e)}")

    def save_rss_items(self, items: List[RSSItem]) -> None:
        """
        Save unique RSSItem objects to DynamoDB.

        Args:
            items (List[RSSItem]): List of RSSItem objects to save.
        """
        self.logger.info(f"Saving {len(items)} RSS items.")
        for item in items:
            try:
                if not self._item_exists(item.link):
                    self.rss_table.put_item(Item=item.model_dump())
                    self.logger.debug(f"Saved RSS item with link: {item.link}")
                else:
                    self.logger.info(f"Item with link {item.link} already exists. Skipping.")
            except ClientError as e:
                self.logger.error(f"Error processing item with link {item.link}: {e.response['Error']['Message']}")
            except Exception as e:
                self.logger.error(f"Unexpected error processing item with link {item.link}: {str(e)}")
        self.logger.info("Completed saving RSS items.")

    def update_rss_item(self, item: RSSItem) -> None:
        """
        Update an existing RSSItem in DynamoDB.

        Args:
            item (RSSItem): RSSItem object to update.
        """
        self.logger.info(f"Updating RSS item with link: {item.link}")
        try:
            self.rss_table.put_item(Item=item.model_dump())
            self.logger.debug(f"Updated RSS item with link: {item.link}")
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
        self.logger.debug("Fetching a random unprocessed RSS item.")
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
            self.logger.debug(f"Selected random item with link: {random_item.get('link')}")
            if 'pub_date' in random_item:
                random_item['pub_date'] = datetime.fromisoformat(random_item['pub_date'])

            return RSSItem(**random_item)
        except ClientError as e:
            self.logger.error(
                f"ClientError querying DynamoDB: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
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
        self.logger.info(f"Retrieving the last {amount} unprocessed RSS items.")
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

            self.logger.debug(f"Retrieved {len(items)} unprocessed RSS items.")
            return [RSSItem(**item) for item in items]
        except ClientError as e:
            self.logger.error(
                f"ClientError querying DynamoDB: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
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
        self.logger.info(f"Retrieving the latest {amount} posts.")
        try:
            response = self.posts_table.scan(
                Limit=amount,
                ProjectionExpression='id, post_time, title, content, tags, source_link'
            )
            items = response.get('Items', [])

            if not items:
                self.logger.info("No posts found.")
                return []

            sorted_items = sorted(items, key=lambda x: x['post_time'], reverse=True)[:amount]
            self.logger.debug(f"Retrieved and sorted {len(sorted_items)} posts.")
            return [Post.from_dynamodb_item(item) for item in sorted_items]
        except ClientError as e:
            self.logger.error(
                f"ClientError querying DynamoDB: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)

        return []

    def get_rss_items(self) -> List[RSSItem]:
        """
        Retrieve all RSSItem objects from DynamoDB.

        Returns:
            List[RSSItem]: List of all RSSItems in the table.
        """
        self.logger.info("Retrieving all RSS items from the table.")
        try:
            response = self.rss_table.scan()
            items = response.get('Items', [])
            self.logger.debug(f"Retrieved {len(items)} RSS items.")
            return [RSSItem(**item) for item in items]
        except ClientError as e:
            self.logger.error(
                f"ClientError scanning DynamoDB: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        except ValidationError as e:
            self.logger.error(f"Error converting DynamoDB items to RSSItems: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")

        return []

    def save_post(self, post: Post) -> None:
        """
        Save a Post object to DynamoDB.

        Args:
            post (Post): Post object to save.
        """
        self.logger.info(f"Saving post with ID: {post.id}")
        try:
            self.posts_table.put_item(Item=post.model_dump())
            self.logger.debug(f"Post saved successfully with ID: {post.id}")
        except ClientError as e:
            self.logger.error(f"Error saving post with ID {post.id}: {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"Unexpected error saving post with ID {post.id}: {str(e)}")

    def _item_exists(self, link: str) -> bool:
        """
        Check if an item with the given link exists in the RSS table.

        Args:
            link (str): The link to check.

        Returns:
            bool: True if the item exists, False otherwise.
        """
        self.logger.debug(f"Checking existence of item with link: {link}")
        try:
            # Cast link to str to ensure compatibility with DynamoDB
            link_str = str(link)

            response = self.rss_table.query(
                IndexName='link-index',
                KeyConditionExpression=Key('link').eq(link_str)
                # Removed ExpressionAttributeValues
            )
            exists = response['Count'] > 0
            self.logger.debug(f"Item with link {link} exists: {exists}")
            return exists
        except ClientError as e:
            self.logger.error(
                f"ClientError checking item existence for link {link}: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"Unexpected error checking item existence for link {link}: {str(e)}")

        return False
