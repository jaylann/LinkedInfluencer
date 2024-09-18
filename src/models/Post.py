import datetime
import uuid
from typing import List

from pydantic import BaseModel, HttpUrl, Field, field_validator

class Post(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str = Field(default="")
    content: str = Field(default="")
    tags: List[str] = Field(default_factory=list)
    source_link: HttpUrl = Field(default="")
    post_time: datetime.datetime = Field(default_factory=datetime.datetime.now, description="The time the post was created.")
    image_link: str = Field(default="", description="The link to the image associated with the post.")

    @classmethod
    def from_dynamodb_item(cls, item: dict) -> 'Post':
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
    def parse_id(cls, value):
        if isinstance(value, str):
            return uuid.UUID(value)
        return value

    @field_validator("source_link", mode="before")
    def parse_source_link(cls, value):
        if isinstance(value, str):
            return value
        return str(value)

    @field_validator('post_time', mode="before")
    def parse_post_time(cls, value):
        if isinstance(value, str):
            return datetime.datetime.fromisoformat(value)
        return value

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        data['id'] = str(self.id)
        data['source_link'] = str(self.source_link)
        data['post_time'] = self.post_time.isoformat()
        return data