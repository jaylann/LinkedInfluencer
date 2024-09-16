import argparse
import logging
import os

from src.models.Post import Post
from src.models.RSSItem import RSSItem
from src.services.ArticleService import ArticleService
from src.services.DynamoDBService import DynamoDBService
from src.services.OpenAIService import OpenAIService
from src.services.RSSService import RSSService
from src.services.S3Service import S3Service


# Main functions
def aggregate_news():
    """Fetches RSS feed and saves all items to DynamoDB."""
    logging.info("Starting RSS feed aggregation")
    rss_service = RSSService()
    logging.info("Fetching RSS feed")
    dynamodb_service = DynamoDBService()
    logging.info("Saving RSS items to DynamoDB")
    rss_items = rss_service.fetch_feed()
    logging.info(f"Found {len(rss_items)} items in RSS feed")
    try:
        dynamodb_service.save_rss_items(rss_items)
    except Exception as e:
        logging.error(f"Error saving RSS items: {e}")

def create_post_from_item(item: RSSItem):
    """Processes a single RSSItem to create a post and updates the RSS feed."""
    article_service = ArticleService()
    openai_service = OpenAIService()
    dynamodb_service = DynamoDBService()
    s3_service = S3Service()

    try:
        article_text = article_service.extract_article_text(item.link)
        post = openai_service.generate_post(article_text, item)
        dynamodb_service.save_post(post)

        # Update RSS feed on S3
        bucket_name = 'linkedin-post-rss-feed'  # Replace with your S3 bucket name
        key = 'rss_feed.xml'                 # Replace with your S3 object key
        s3_service.update_rss_feed(bucket_name, key, post)
    except Exception as e:
        print(f"Error processing {item.link}: {e}")

def process_rss_items():
    """Retrieves items from DynamoDB and processes each item."""
    dynamodb_service = DynamoDBService()

    openai_service = OpenAIService()
    chosen_item = dynamodb_service.get_random_unprocessed_item()
    if chosen_item:
        logging.info(f"Processing item: {chosen_item.link}")
        create_post_from_item(chosen_item)
        chosen_item.processed = True
        dynamodb_service.update_rss_item(chosen_item)
    else:
        logging.info("No unprocessed items found in DynamoDB")

def main(action):
    if action == 'aggregate_news':
        aggregate_news()
    elif action == 'process_items':
        process_rss_items()
    else:
        print(f"Unknown action: {action}. Please use 'aggregate_news' or 'process_items'.")

# Set up basic logging
logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context):
    """Lambda handler that determines action based on environment variable."""
    logging.info("Lambda handler started")
    action = os.getenv('ACTION', 'aggregate_news')  # Default to 'aggregate_news'
    logging.info(f"Action determined: {action}")
    try:
        if action == 'aggregate_news':
            logging.info("Aggregating news")
            try:
                aggregate_news()
            except Exception as e:
                logging.error(f"Error aggregating news: {e}")
        elif action == 'process_items':
            process_rss_items()
        else:
            logging.error(f"Unknown action: {action}. Please use 'aggregate_news' or 'process_items'.")
    except Exception as e:
        logging.error(f"Exception in lambda_handler: {str(e)}")
        raise
    result = {"status": "success", "message": "Items saved to DynamoDB"}
    return result

if __name__ == "__main__":
    print("Running main script")
    # Check if running in an environment that sets the ACTION variable
    if os.getenv("AWS_EXECUTION_ENV"):
        lambda_handler({}, None)
    else:
        parser = argparse.ArgumentParser(description='Run RSS feed aggregator and processor.')
        parser.add_argument('action', choices=['aggregate_news', 'process_items'], help='Action to perform.')
        args = parser.parse_args()
        main(args.action)