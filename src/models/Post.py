import datetime
import uuid
from typing import List, overload

from pydantic import BaseModel, HttpUrl, Field
from typing_extensions import override


class Post(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    source_link: HttpUrl
    post_time: datetime.datetime = Field(default=datetime.datetime.now(), description="The time the post was created.")

    def model_dump(self, **kwargs):
        # Call the super().model_dump() to get the original dictionary
        data = super().model_dump(**kwargs)
        # Convert id, link, and pub_date to strings
        data['id'] = str(self.id)
        data['source_link'] = str(self.source_link)
        # Convert pub_date to ISO 8601 string
        data['post_time'] = self.post_time.isoformat()
        return data
