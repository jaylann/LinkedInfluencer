import argparse
import logging
from typing import List, Tuple
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

from src.models.RSSItem import RSSItem
from src.services.ArticleService import ArticleService
from src.services.DynamoDBService import DynamoDBService
from src.services.OpenAIService import OpenAIService
from src.models.OpenAIConfig import OpenAIConfig
from src.services.RSSService import RSSService
from src.services.S3Service import S3Service

load_dotenv(".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppConfig(BaseModel):
    """Application configuration."""
    bucket_name: str = Field(..., description="S3 bucket name for RSS feed")
    rss_feed_key: str = Field(..., description="S3 object key for RSS feed")

config = AppConfig(
    bucket_name=os.getenv("S3_BUCKET_NAME", "linkedin-post-rss-feed"),
    rss_feed_key=os.getenv("RSS_FEED_KEY", "rss_feed.xml")
)

def aggregate_news() -> None:
    """Fetches RSS feeds and saves all items to DynamoDB."""
    logger.info("Starting RSS feed aggregation")
    rss_service = RSSService()
    dynamodb_service = DynamoDBService()

    try:
        rss_items: List[RSSItem] = rss_service.fetch_tech_crunch() + rss_service.fetch_ars_technica()
        logger.info(f"Found {len(rss_items)} items in RSS feeds")
        dynamodb_service.save_rss_items(rss_items)
    except Exception as e:
        logger.error(f"Error aggregating news: {e}")
        raise

def create_post_from_item(item: RSSItem) -> None:
    """Processes a single RSSItem to create a post and updates the RSS feed."""
    openai_service = OpenAIService(OpenAIConfig())
    dynamodb_service = DynamoDBService()
    s3_service = S3Service()

    try:
        article_text, image_link = extract_article_content(str(item.link))
        post = openai_service.generate_post(article_text, item)
        post.image_link = image_link
        dynamodb_service.save_post(post)
        s3_service.update_rss_feed(config.bucket_name, config.rss_feed_key, post)
    except Exception as e:
        logger.error(f"Error processing {item.link}: {e}")

def extract_article_content(link: str) -> Tuple[str, str]:
    """Extracts article text and image link based on the source."""
    if 'techcrunch' in link:
        return ArticleService.extract_techcrunch_article(link)
    return ArticleService.extract_arstechnica_article(link)

def process_rss_items() -> None:
    """Retrieves items from DynamoDB and processes each item."""
    dynamodb_service = DynamoDBService()
    openai_service = OpenAIService(OpenAIConfig())

    already_posted = dynamodb_service.get_latest_posts(10)
    choosable = dynamodb_service.get_last_unprocessed_rss_items(20)
    chosen_item = openai_service.choose_post(choosable, already_posted)

    if chosen_item:
        logger.info(f"Processing item: {chosen_item.link}")
        create_post_from_item(chosen_item)
        chosen_item.processed = True
        dynamodb_service.update_rss_item(chosen_item)
    else:
        logger.info("No unprocessed items found in DynamoDB")

def main(action: str) -> None:
    """Main function to run the appropriate action."""
    actions = {
        'aggregate_news': aggregate_news,
        'process_items': process_rss_items
    }
    if action not in actions:
        logger.error(f"Unknown action: {action}. Please use 'aggregate_news' or 'process_items'.")
        return
    actions[action]()

def lambda_handler(event: dict, context: object) -> dict:
    """AWS Lambda handler that determines action based on environment variable."""
    logger.info("Lambda handler started")
    action = os.getenv('ACTION', 'aggregate_news')
    logger.info(f"Action determined: {action}")

    try:
        main(action)
    except Exception as e:
        logger.error(f"Exception in lambda_handler: {str(e)}")
        raise

    return {"status": "success", "message": "Operation completed successfully"}

if __name__ == "__main__":
    logger.info("Running main script")
    if os.getenv("AWS_EXECUTION_ENV"):
        lambda_handler({}, None)
    else:
        parser = argparse.ArgumentParser(description='Run RSS feed aggregator and processor.')
        parser.add_argument('action', choices=['aggregate_news', 'process_items'], help='Action to perform.')
        args = parser.parse_args()
        main(args.action)