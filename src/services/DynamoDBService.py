import logging
import random
from datetime import datetime
from typing import List, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from src.models.RSSItem import RSSItem
from src.models.Post import Post


class DynamoDBService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')

    def save_rss_items(self, items: List[RSSItem]) -> None:
        """
        Saves a list of unique RSSItem objects to DynamoDB.

        This method checks for existing items with the same link using a GSI
        and only saves new items to avoid duplicates.
        """
        table = self.dynamodb.Table('rss-feed-scraped-articles')

        for item in items:
            try:
                # Check if an item with the same link already exists
                response = table.query(
                    IndexName='link-index',
                    KeyConditionExpression='link = :link',
                    ExpressionAttributeValues={':link': str(item.link)}
                )

                if response['Count'] == 0:
                    # Item doesn't exist, so we can save it
                    item_dict = item.model_dump()
                    table.put_item(Item=item_dict)
                else:
                    print(f"Item with link {item.link} already exists. Skipping.")

            except ClientError as e:
                print(f"Error processing item with link {item.link}: {e.response['Error']['Message']}")
            except Exception as e:
                print(f"Unexpected error processing item with link {item.link}: {str(e)}")

    def update_rss_item(self, item: RSSItem) -> None:
        """
        Saves a list of unique RSSItem objects to DynamoDB.

        This method checks for existing items with the same link using a GSI
        and only saves new items to avoid duplicates.
        """
        table = self.dynamodb.Table('rss-feed-scraped-articles')


        try:
            # Check if an item with the same link already exists

            item_dict = item.model_dump()
            table.put_item(Item=item_dict)

        except ClientError as e:
            print(f"Error processing item with link {item.link}: {e.response['Error']['Message']}")
        except Exception as e:
            print(f"Unexpected error processing item with link {item.link}: {str(e)}")

    def get_random_unprocessed_item(self) -> Optional[RSSItem]:
        """
        Retrieves a single random unprocessed item from the DynamoDB table.

        Returns:
            Optional[RSSItem]: A random unprocessed RSSItem if available, None otherwise.
        """
        table = self.dynamodb.Table('rss-feed-scraped-articles')

        try:
            # Query for unprocessed items
            response = table.query(
                IndexName='processed-id-index',
                KeyConditionExpression=Key('processed').eq(0),  # Use string 'false' instead of boolean False
                Limit=20  # Adjust this value based on your needs
            )

            items = response.get('Items', [])

            if not items:
                print("No unprocessed items found.")
                return None

            # Select a random item
            random_item = random.choice(items)
            print(random_item)
            # Convert the ISO date string back to datetime
            if 'pub_date' in random_item:
                random_item['pub_date'] = datetime.fromisoformat(random_item['pub_date'])
            print(random_item)

            # Convert the DynamoDB item to an RSSItem
            try:
                return RSSItem(**random_item)
            except Exception as e:
                print(f"Error converting DynamoDB item to RSSItem: {str(e)}")
                return None

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"ClientError querying DynamoDB: {error_code} - {error_message}")
            return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None

    def get_last_unprocessed_rss_items(self, amount: int) -> Optional[List[RSSItem]]:
        """
        Retrieves a single random unprocessed item from the DynamoDB table.

        Returns:
            Optional[RSSItem]: A random unprocessed RSSItem if available, None otherwise.
        """
        table = self.dynamodb.Table('rss-feed-scraped-articles')

        try:
            # Query for unprocessed items
            response = table.query(
                IndexName='processed-pub_date-index',
                KeyConditionExpression=Key('processed').eq(0),
                ScanIndexForward=False,  # Sort in descending order (newest first)
                Limit=amount
            )

            items = response.get('Items', [])

            if not items:
                print("No unprocessed items found.")
                return None


            # Convert the DynamoDB item to an RSSItem
            try:
                return [RSSItem(**item) for item in items]
            except Exception as e:
                print(f"Error converting DynamoDB item to RSSItem: {str(e)}")
                return None

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"ClientError querying DynamoDB: {error_code} - {error_message}")
            return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None


    def get_latest_posts(self, amount: int) -> List[Post]:
        """
        Retrieves the latest posts from the LinkedIn automation posts table.

        Args:
            amount (int): The number of posts to retrieve.

        Returns:
            List[Post]: A list of the latest Post objects.
        """
        try:
            table = self.dynamodb.Table('linkedin-automation-posts')
            response = table.scan(
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
        """Retrieves all RSSItem objects from DynamoDB."""
        table = self.dynamodb.Table('rss-feed-scraped-articles')
        response = table.scan()
        items = response.get('Items', [])
        return [RSSItem(**item) for item in items]

    def save_post(self, post: Post):
        """Saves a Post object to DynamoDB."""
        table = self.dynamodb.Table('linkedin-automation-posts')
        table.put_item(Item=post.model_dump())
