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
    rss_service = RSSService()
    dynamodb_service = DynamoDBService()
    rss_items = rss_service.fetch_feed()
    dynamodb_service.save_rss_items(rss_items)

def create_post_from_item(item: RSSItem):
    """Processes a single RSSItem to create a post and updates the RSS feed."""
    article_service = ArticleService()
    openai_service = OpenAIService()
    dynamodb_service = DynamoDBService()
    s3_service = S3Service()

    try:
        article_text = article_service.extract_article_text(item.link)
        viral_post_content = openai_service.generate_post(article_text)
        post = Post(content=viral_post_content, source_link=item.link)
        dynamodb_service.save_post(post)

        # Update RSS feed on S3
        bucket_name = 'your-s3-bucket-name'  # Replace with your S3 bucket name
        key = 'rss_feed.xml'                 # Replace with your S3 object key
        s3_service.update_rss_feed(bucket_name, key, post)
    except Exception as e:
        print(f"Error processing {item.link}: {e}")

# Example usage
if __name__ == "__main__":
    # Step 1: Aggregate news and save to DynamoDB
    aggregate_news()

    # Step 2: Retrieve items from DynamoDB and process each item
    #dynamodb_service = DynamoDBService()
    #rss_items = dynamodb_service.get_rss_items()

    #for item in rss_items:
    #    create_post_from_item(item)