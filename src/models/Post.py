from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator

class Post(BaseModel):
    """
    Represents a blog post with various attributes.
    """

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(default="")
    content: str = Field(default="")
    tags: List[str] = Field(default_factory=list)
    source_link: HttpUrl = Field(default="")
    post_time: datetime = Field(
        default_factory=datetime.now,
        description="The time the post was created."
    )
    image_link: str = Field(
        default="",
        description="The link to the image associated with the post."
    )

    @classmethod
    def from_dynamodb_item(cls, item: dict) -> 'Post':
        """
        Create a Post instance from a DynamoDB item.

        Args:
            item (dict): The DynamoDB item representing a post.

        Returns:
            Post: A new Post instance.
        """
        return cls(
            id=item['id'],
            post_time=item['post_time'],
            title=item['title'],
            content=item['content'],
            tags=item['tags'],
            source_link=item['source_link'],
            image_link=item.get('image_link', "")
        )

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, value):
        """Convert string to UUID if necessary."""
        return UUID(value) if isinstance(value, str) else value

    @field_validator("source_link", mode="before")
    @classmethod
    def parse_source_link(cls, value):
        """Ensure source_link is a string."""
        return str(value)

    @field_validator('post_time', mode="before")
    @classmethod
    def parse_post_time(cls, value):
        """Convert string to datetime if necessary."""
        return datetime.fromisoformat(value) if isinstance(value, str) else value

    def model_dump(self, **kwargs):
        """
        Serialize the model, converting certain fields to string representation.

        Returns:
            dict: Serialized model data.
        """
        data = super().model_dump(**kwargs)
        data['id'] = str(self.id)
        data['source_link'] = str(self.source_link)
        data['post_time'] = self.post_time.isoformat()
        return data


