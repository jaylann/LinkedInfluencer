from pydantic import BaseModel, Field


class RSSFeed(BaseModel):
    """Represents the structure of an RSS feed."""
    title: str = Field(default="Justin Lanfermann LinkedIn Feed")
    link: str = Field(default="https://www.linkedin.com/in/justin-lanfermann-07352124b/")
    description: str = Field(default="Here I post the most exciting pieces of news in the tech world!")
    language: str = Field(default="en-us")