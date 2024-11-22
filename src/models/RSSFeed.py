import os

from pydantic import BaseModel, Field

#==============================================================
# This RSSFeed class represents YOUR RSS Feed.
# Change the Field defaults accordingly.
#
# On the first run the S3Service will use
# these defaults to create your RSS Feed
#==============================================================


class RSSFeed(BaseModel):
    """Represents the structure of YOUR RSS feed."""
    title: str = Field(default=os.getenv("RSS_FEED_TITLE", "My RSS Feed"))
    link: str = Field(default=os.getenv("RSS_FEED_LINK", "https://www.example.com/rss"))
    description: str = Field(default=os.getenv("RSS_FEED_DESCRIPTION", "The latest news from my website."))
    language: str = Field(default="en-us")